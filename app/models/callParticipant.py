from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Float, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class ParticipantRole(str, enum.Enum):
    host = "host"                # Animateur principal
    co_host = "co_host"         # Co-animateur
    participant = "participant"  # Participant standard
    observer = "observer"       # Observateur (écoute seulement)

class ParticipantStatus(str, enum.Enum):
    invited = "invited"         # Invité mais pas encore répondu
    confirmed = "confirmed"     # Confirmé sa présence
    declined = "declined"       # A décliné l'invitation
    attended = "attended"       # A participé
    no_show = "no_show"        # Absence non excusée
    left_early = "left_early"  # Parti avant la fin

class CallParticipant(Base):
    __tablename__ = "call_participants"

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relations
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.call_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=True)  # Si expert invité
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)  # Référence générale
    
    # Rôle et statut
    role = Column(Enum(ParticipantRole), default=ParticipantRole.participant)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.invited)
    
    # Invitation
    invited_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    invitation_sent = Column(Boolean, default=False)
    
    # Réponse à l'invitation
    responded_at = Column(DateTime, nullable=True)
    response_message = Column(Text, nullable=True)  # Message optionnel de réponse
    
    # Participation effective
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Paramètres techniques
    camera_enabled = Column(Boolean, default=True)
    microphone_enabled = Column(Boolean, default=True)
    screen_sharing_used = Column(Boolean, default=False)
    
    # Engagement
    questions_asked = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)  # Messages dans le chat
    polls_answered = Column(Integer, default=0)
    
    # Évaluation
    satisfaction_rating = Column(Float, nullable=True)  # Note de 1 à 5
    feedback = Column(Text, nullable=True)
    would_recommend = Column(Boolean, nullable=True)
    
    # Suivi post-session
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)
    next_meeting_scheduled = Column(DateTime, nullable=True)
    
    # Relations
    call = relationship("Call", back_populates="participants")
    entrepreneur = relationship("Entrepreneur", back_populates="call_participations")
    expert = relationship("Expert")
    user = relationship("User")
    invited_by_user = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<CallParticipant {self.user_id} in {self.call_id}>"
    
    @property
    def display_name(self) -> str:
        """Nom d'affichage du participant"""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return "Participant"
    
    @property
    def attended_full_session(self) -> bool:
        """Vérifier si a assisté à toute la session"""
        if not self.joined_at or not self.left_at or not self.call:
            return False
        
        # Tolérance de 10% de la durée totale
        total_duration = (self.call.scheduled_end - self.call.scheduled_start).total_seconds() / 60
        attended_duration = self.actual_duration_minutes or 0
        
        return attended_duration >= (total_duration * 0.9)
    
    @property
    def engagement_score(self) -> float:
        """Score d'engagement calculé"""
        score = 0.0
        
        # Présence (40% du score)
        if self.status == ParticipantStatus.attended:
            if self.attended_full_session:
                score += 40
            else:
                score += 20
        
        # Participation active (60% du score)
        if self.questions_asked > 0:
            score += min(self.questions_asked * 5, 20)  # Max 20 points
        
        if self.messages_sent > 0:
            score += min(self.messages_sent * 2, 15)  # Max 15 points
        
        if self.polls_answered > 0:
            score += min(self.polls_answered * 3, 15)  # Max 15 points
        
        if self.camera_enabled:
            score += 5
        
        if self.microphone_enabled:
            score += 5
        
        return min(score, 100.0)