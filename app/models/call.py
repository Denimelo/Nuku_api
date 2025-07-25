from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class CallType(str, enum.Enum):
    one_on_one = "one_on_one"        # Session 1:1 entrepreneur-expert
    group_session = "group_session"   # Session de groupe dans un programme
    webinar = "webinar"              # Webinaire (un présentateur, plusieurs participants)
    workshop = "workshop"            # Atelier interactif
    office_hours = "office_hours"    # Permanence expert

class CallStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class CallPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class Call(Base):
    __tablename__ = "calls"

    call_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Métadonnées de base
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agenda = Column(Text, nullable=True)  # Ordre du jour
    
    # Type et configuration
    call_type = Column(Enum(CallType), nullable=False)
    priority = Column(Enum(CallPriority), default=CallPriority.normal)
    
    # Planification
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="UTC")  # Fuseau horaire
    
    # Durée et timing réels
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Durée planifiée
    actual_duration_minutes = Column(Integer, nullable=True)  # Durée réelle
    
    # Configuration technique
    meeting_url = Column(String(500), nullable=True)  # URL de la réunion (Zoom, Teams, etc.)
    meeting_id = Column(String(100), nullable=True)   # ID de la réunion externe
    meeting_password = Column(String(50), nullable=True)  # Mot de passe si nécessaire
    platform = Column(String(50), default="zoom")     # zoom, teams, meet, jitsi, etc.
    
    # Récurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Configuration récurrence
    parent_call_id = Column(UUID(as_uuid=True), ForeignKey("calls.call_id"), nullable=True)  # Appel parent si récurrent
    
    # Relations et contexte
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)  # Animateur principal
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # États et restrictions
    status = Column(Enum(CallStatus), default=CallStatus.scheduled)
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, nullable=True)  # Limite de participants
    requires_approval = Column(Boolean, default=False)  # Inscription nécessite approbation
    is_recorded = Column(Boolean, default=False)
    recording_url = Column(String(500), nullable=True)
    
    # Notifications et rappels
    reminder_sent = Column(Boolean, default=False)
    reminder_minutes_before = Column(Integer, default=15)  # Rappel X minutes avant
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes post-session
    summary = Column(Text, nullable=True)  # Résumé de la session
    next_steps = Column(Text, nullable=True)  # Actions à suivre
    follow_up_date = Column(DateTime, nullable=True)  # Date de suivi
    
    # Statistiques
    participant_count = Column(Integer, default=0)
    attendance_rate = Column(Float, default=0.0)  # Taux de présence
    satisfaction_score = Column(Float, nullable=True)  # Note de satisfaction moyenne
    
    # Relations
    program = relationship("Program", back_populates="calls")
    module = relationship("Module")
    expert = relationship("Expert", back_populates="calls_hosted", foreign_keys=[expert_id])
    created_by_user = relationship("User")
    participants = relationship("CallParticipant", back_populates="call", cascade="all, delete-orphan")
    
    # Auto-référence pour récurrence
    child_calls = relationship("Call", backref="parent_call", remote_side=[call_id])

    def __repr__(self):
        return f"<Call {self.title} - {self.scheduled_start}>"
    
    @property
    def is_upcoming(self) -> bool:
        """Vérifier si l'appel est à venir"""
        return self.scheduled_start > datetime.utcnow() and self.status == CallStatus.scheduled
    
    @property
    def is_live(self) -> bool:
        """Vérifier si l'appel est en cours"""
        now = datetime.utcnow()
        return (self.scheduled_start <= now <= self.scheduled_end and 
                self.status == CallStatus.in_progress)
    
    @property
    def is_past(self) -> bool:
        """Vérifier si l'appel est terminé"""
        return (self.scheduled_end < datetime.utcnow() or 
                self.status in [CallStatus.completed, CallStatus.cancelled])
    
    @property
    def duration_planned(self) -> timedelta:
        """Durée planifiée"""
        return self.scheduled_end - self.scheduled_start
    
    @property
    def time_until_start(self) -> timedelta:
        """Temps avant le début"""
        if self.is_upcoming:
            return self.scheduled_start - datetime.utcnow()
        return timedelta(0)
    
    @property
    def can_join(self) -> bool:
        """Vérifier si on peut rejoindre l'appel"""
        now = datetime.utcnow()
        # Autoriser de rejoindre 5 minutes avant et jusqu'à la fin
        join_window_start = self.scheduled_start - timedelta(minutes=5)
        return (join_window_start <= now <= self.scheduled_end and 
                self.status in [CallStatus.scheduled, CallStatus.in_progress])