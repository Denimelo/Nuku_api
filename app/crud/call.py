from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, extract
from uuid import UUID
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from app.models.call import Call, CallType, CallStatus, CallPriority
from app.models.callParticipant import CallParticipant, ParticipantRole, ParticipantStatus
from app.models.callRecording import CallRecording
from app.models.user import User
from app.models.expert import Expert
from app.models.entrepreneur import Entrepreneur
from app.schemas.call import CallCreate, CallUpdate, CallParticipantCreate, CallParticipantUpdate, CallFilter

# ========== CRUD CALL ==========

def create_call(
    db: Session,
    call_data: CallCreate,
    created_by: UUID,
    expert_id: Optional[UUID] = None
) -> Call:
    """Créer un nouvel appel"""
    
    # Utiliser expert_id fourni ou déduire depuis created_by
    if not expert_id:
        expert = db.query(Expert).join(User).filter(User.user_id == created_by).first()
        if expert:
            expert_id = expert.expert_id
        else:
            raise ValueError("Expert non trouvé")
    
    # Calculer durée planifiée
    duration = (call_data.scheduled_end - call_data.scheduled_start).total_seconds() / 60
    
    call = Call(
        title=call_data.title,
        description=call_data.description,
        agenda=call_data.agenda,
        call_type=call_data.call_type,
        priority=call_data.priority,
        scheduled_start=call_data.scheduled_start,
        scheduled_end=call_data.scheduled_end,
        timezone=call_data.timezone,
        duration_minutes=int(duration),
        program_id=call_data.program_id,
        module_id=call_data.module_id,
        expert_id=expert_id,
        created_by=created_by,
        max_participants=call_data.max_participants,
        requires_approval=call_data.requires_approval,
        is_recorded=call_data.is_recorded,
        platform=call_data.platform,
        reminder_minutes_before=call_data.reminder_minutes_before
    )
    
    db.add(call)
    db.flush()  # Pour avoir l'ID
    
    # Ajouter le créateur comme host
    host_participant = CallParticipant(
        call_id=call.call_id,
        user_id=created_by,
        expert_id=expert_id,
        role=ParticipantRole.host,
        status=ParticipantStatus.confirmed,
        invitation_sent=True
    )
    db.add(host_participant)
    
    # Inviter participants si spécifiés
    if call_data.participant_ids:
        for participant_id in call_data.participant_ids:
            participant = CallParticipant(
                call_id=call.call_id,
                user_id=participant_id,
                role=ParticipantRole.participant,
                invited_by=created_by
            )
            
            # Déterminer si entrepreneur ou expert
            entrepreneur = db.query(Entrepreneur).join(User).filter(User.user_id == participant_id).first()
            if entrepreneur:
                participant.entrepreneur_id = entrepreneur.entrepreneur_id
            
            db.add(participant)
    
    # Mettre à jour compteur de participants
    call.participant_count = len(call_data.participant_ids or []) + 1  # +1 pour le host
    
    db.commit()
    db.refresh(call)
    return call

def get_call_by_id(db: Session, call_id: UUID) -> Optional[Call]:
    """Récupérer appel par ID avec relations"""
    return db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user),
        joinedload(Call.program),
        joinedload(Call.module),
        joinedload(Call.created_by_user),
        joinedload(Call.participants).joinedload(CallParticipant.user)
    ).filter(Call.call_id == call_id).first()

def get_calls_by_expert(
    db: Session,
    expert_id: UUID,
    include_past: bool = True,
    limit: int = 50
) -> List[Call]:
    """Appels d'un expert (créés ou où il est invité)"""
    
    query = db.query(Call).options(
        joinedload(Call.program),
        joinedload(Call.participants)
    ).filter(
        or_(
            Call.expert_id == expert_id,
            Call.participants.any(CallParticipant.expert_id == expert_id)
        )
    )
    
    if not include_past:
        query = query.filter(Call.scheduled_start >= datetime.utcnow())
    
    return query.order_by(desc(Call.scheduled_start)).limit(limit).all()

def get_calls_by_entrepreneur(
    db: Session,
    entrepreneur_id: UUID,
    include_past: bool = True,
    limit: int = 50
) -> List[Call]:
    """Appels d'un entrepreneur"""
    
    query = db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user),
        joinedload(Call.program),
        joinedload(Call.participants)
    ).join(CallParticipant).filter(
        CallParticipant.entrepreneur_id == entrepreneur_id
    )
    
    if not include_past:
        query = query.filter(Call.scheduled_start >= datetime.utcnow())
    
    return query.order_by(desc(Call.scheduled_start)).limit(limit).all()

def get_calls_by_program(
    db: Session,
    program_id: UUID,
    upcoming_only: bool = False
) -> List[Call]:
    """Appels d'un programme"""
    
    query = db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user),
        joinedload(Call.participants)
    ).filter(Call.program_id == program_id)
    
    if upcoming_only:
        query = query.filter(Call.scheduled_start >= datetime.utcnow())
    
    return query.order_by(Call.scheduled_start).all()

def get_upcoming_calls(
    db: Session,
    user_id: UUID,
    days_ahead: int = 7
) -> List[Call]:
    """Appels à venir pour un utilisateur"""
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=days_ahead)
    
    return db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user),
        joinedload(Call.program)
    ).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.scheduled_start.between(start_time, end_time),
        Call.status == CallStatus.scheduled
    ).order_by(Call.scheduled_start).all()

def update_call(
    db: Session,
    call_id: UUID,
    update_data: CallUpdate,
    user_id: UUID
) -> Optional[Call]:
    """Mettre à jour un appel"""
    
    call = db.query(Call).filter(Call.call_id == call_id).first()
    
    if not call:
        return None
    
    # TODO: Vérifier permissions (créateur, host, ou admin)
    
    # Mettre à jour champs
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(call, field):
            setattr(call, field, value)
    
    # Recalculer durée si dates modifiées
    if update_data.scheduled_start or update_data.scheduled_end:
        duration = (call.scheduled_end - call.scheduled_start).total_seconds() / 60
        call.duration_minutes = int(duration)
    
    call.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(call)
    return call

def cancel_call(
    db: Session,
    call_id: UUID,
    user_id: UUID,
    reason: Optional[str] = None
) -> Optional[Call]:
    """Annuler un appel"""
    
    call = db.query(Call).filter(Call.call_id == call_id).first()
    
    if not call:
        return None
    
    # TODO: Vérifier permissions et statut
    
    call.status = CallStatus.cancelled
    if reason:
        call.summary = f"Annulé: {reason}"
    call.updated_at = datetime.utcnow()
    
    # Mettre à jour participants
    db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.status.in_([ParticipantStatus.invited, ParticipantStatus.confirmed])
    ).update({"status": ParticipantStatus.declined})
    
    db.commit()
    db.refresh(call)
    return call

def start_call(db: Session, call_id: UUID, user_id: UUID) -> Optional[Call]:
    """Démarrer un appel"""
    
    call = db.query(Call).filter(Call.call_id == call_id).first()
    
    if not call or call.status != CallStatus.scheduled:
        return None
    
    call.status = CallStatus.in_progress
    call.actual_start = datetime.utcnow()
    call.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(call)
    return call

def end_call(
    db: Session, 
    call_id: UUID, 
    user_id: UUID,
    summary: Optional[str] = None,
    next_steps: Optional[str] = None
) -> Optional[Call]:
    """Terminer un appel"""
    
    call = db.query(Call).filter(Call.call_id == call_id).first()
    
    if not call or call.status != CallStatus.in_progress:
        return None
    
    now = datetime.utcnow()
    call.status = CallStatus.completed
    call.actual_end = now
    
    if call.actual_start:
        call.actual_duration_minutes = int((now - call.actual_start).total_seconds() / 60)
    
    if summary:
        call.summary = summary
    
    if next_steps:
        call.next_steps = next_steps
    
    # Calculer taux de présence
    total_invited = db.query(CallParticipant).filter(CallParticipant.call_id == call_id).count()
    attended = db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.status == ParticipantStatus.attended
    ).count()
    
    call.attendance_rate = (attended / total_invited * 100) if total_invited > 0 else 0
    call.updated_at = now
    
    db.commit()
    db.refresh(call)
    return call

# ========== CRUD CALL PARTICIPANT ==========

def invite_participants(
    db: Session,
    call_id: UUID,
    participant_ids: List[UUID],
    invited_by: UUID,
    role: ParticipantRole = ParticipantRole.participant
) -> Tuple[int, int, List[str]]:
    """Inviter participants à un appel"""
    
    call = get_call_by_id(db, call_id)
    if not call:
        return 0, 0, ["Appel non trouvé"]
    
    invited_count = 0
    already_invited_count = 0
    failed_invitations = []
    
    for participant_id in participant_ids:
        # Vérifier si déjà invité
        existing = db.query(CallParticipant).filter(
            CallParticipant.call_id == call_id,
            CallParticipant.user_id == participant_id
        ).first()
        
        if existing:
            already_invited_count += 1
            continue
        
        # Vérifier que l'utilisateur existe
        user = db.query(User).filter(User.user_id == participant_id).first()
        if not user:
            failed_invitations.append(f"Utilisateur {participant_id} non trouvé")
            continue
        
        # Créer participation
        participant = CallParticipant(
            call_id=call_id,
            user_id=participant_id,
            role=role,
            invited_by=invited_by
        )
        
        # Déterminer type d'utilisateur
        entrepreneur = db.query(Entrepreneur).join(User).filter(User.user_id == participant_id).first()
        expert = db.query(Expert).join(User).filter(User.user_id == participant_id).first()
        
        if entrepreneur:
            participant.entrepreneur_id = entrepreneur.entrepreneur_id
        elif expert:
            participant.expert_id = expert.expert_id
        
        db.add(participant)
        invited_count += 1
    
    # Mettre à jour compteur
    call.participant_count = db.query(CallParticipant).filter(CallParticipant.call_id == call_id).count()
    
    db.commit()
    return invited_count, already_invited_count, failed_invitations

def respond_to_invitation(
    db: Session,
    call_id: UUID,
    user_id: UUID,
    status: ParticipantStatus,
    message: Optional[str] = None
) -> Optional[CallParticipant]:
    """Répondre à une invitation"""
    
    participant = db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.user_id == user_id
    ).first()
    
    if not participant:
        return None
    
    participant.status = status
    participant.responded_at = datetime.utcnow()
    participant.response_message = message
    
    db.commit()
    db.refresh(participant)
    return participant

def join_call(
    db: Session,
    call_id: UUID,
    user_id: UUID
) -> Optional[CallParticipant]:
    """Rejoindre un appel"""
    
    participant = db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.user_id == user_id
    ).first()
    
    if not participant:
        return None
    
    participant.joined_at = datetime.utcnow()
    participant.status = ParticipantStatus.attended
    
    db.commit()
    db.refresh(participant)
    return participant

def leave_call(
    db: Session,
    call_id: UUID,
    user_id: UUID
) -> Optional[CallParticipant]:
    """Quitter un appel"""
    
    participant = db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.user_id == user_id
    ).first()
    
    if not participant or not participant.joined_at:
        return None
    
    now = datetime.utcnow()
    participant.left_at = now
    
    # Calculer durée de participation
    duration = (now - participant.joined_at).total_seconds() / 60
    participant.actual_duration_minutes = int(duration)
    
    db.commit()
    db.refresh(participant)
    return participant

def update_participant(
    db: Session,
    participant_id: UUID,
    update_data: CallParticipantUpdate
) -> Optional[CallParticipant]:
    """Mettre à jour participant"""
    
    participant = db.query(CallParticipant).filter(
        CallParticipant.participant_id == participant_id
    ).first()
    
    if not participant:
        return None
    
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(participant, field):
            setattr(participant, field, value)
    
    db.commit()
    db.refresh(participant)
    return participant

def get_call_participants(
    db: Session,
    call_id: UUID,
    role: Optional[ParticipantRole] = None
) -> List[CallParticipant]:
    """Participants d'un appel"""
    
    query = db.query(CallParticipant).options(
        joinedload(CallParticipant.user),
        joinedload(CallParticipant.entrepreneur),
        joinedload(CallParticipant.expert)
    ).filter(CallParticipant.call_id == call_id)
    
    if role:
        query = query.filter(CallParticipant.role == role)
    
    return query.all()

def remove_participant(
    db: Session,
    call_id: UUID,
    user_id: UUID,
    removed_by: UUID
) -> bool:
    """Retirer un participant"""
    
    participant = db.query(CallParticipant).filter(
        CallParticipant.call_id == call_id,
        CallParticipant.user_id == user_id
    ).first()
    
    if not participant:
        return False
    
    db.delete(participant)
    
    # Mettre à jour compteur
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if call:
        call.participant_count -= 1
    
    db.commit()
    return True

# ========== RECHERCHE ET FILTRES ==========

def search_calls(
    db: Session,
    user_id: UUID,
    filters: CallFilter,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Call], int]:
    """Rechercher appels avec filtres"""
    
    query = db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user),
        joinedload(Call.program)
    ).join(CallParticipant).filter(CallParticipant.user_id == user_id)
    
    # Appliquer filtres
    if filters.call_type:
        query = query.filter(Call.call_type == filters.call_type)
    
    if filters.status:
        query = query.filter(Call.status == filters.status)
    
    if filters.program_id:
        query = query.filter(Call.program_id == filters.program_id)
    
    if filters.expert_id:
        query = query.filter(Call.expert_id == filters.expert_id)
    
    if filters.date_from:
        query = query.filter(Call.scheduled_start >= filters.date_from)
    
    if filters.date_to:
        query = query.filter(Call.scheduled_start <= filters.date_to)
    
    # Compter total
    total_count = query.count()
    
    # Récupérer résultats paginés
    calls = query.order_by(desc(Call.scheduled_start)).offset(skip).limit(limit).all()
    
    return calls, total_count

def get_calendar_calls(
    db: Session,
    user_id: UUID,
    year: int,
    month: int
) -> Dict[int, List[Call]]:
    """Appels d'un mois pour calendrier"""
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    calls = db.query(Call).options(
        joinedload(Call.expert).joinedload(Expert.user)
    ).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.scheduled_start >= start_date,
        Call.scheduled_start < end_date
    ).order_by(Call.scheduled_start).all()
    
    # Grouper par jour
    calendar_data = {}
    for call in calls:
        day = call.scheduled_start.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append(call)
    
    return calendar_data

# ========== STATISTIQUES ==========

def get_call_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
    """Statistiques d'appels pour un utilisateur"""
    
    # Appels totaux
    total_calls = db.query(Call).join(CallParticipant).filter(
        CallParticipant.user_id == user_id
    ).count()
    
    # Par statut
    upcoming = db.query(Call).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.scheduled_start > datetime.utcnow(),
        Call.status == CallStatus.scheduled
    ).count()
    
    completed = db.query(Call).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.completed
    ).count()
    
    cancelled = db.query(Call).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.cancelled
    ).count()
    
    # Participants totaux (si expert)
    total_participants = db.query(func.sum(Call.participant_count)).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.completed
    ).scalar() or 0
    
    # Durée moyenne
    avg_duration = db.query(func.avg(Call.actual_duration_minutes)).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.completed,
        Call.actual_duration_minutes.isnot(None)
    ).scalar() or 0
    
    # Taux de présence moyen
    avg_attendance = db.query(func.avg(Call.attendance_rate)).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.completed
    ).scalar() or 0
    
    # Satisfaction moyenne
    avg_satisfaction = db.query(func.avg(Call.satisfaction_score)).join(CallParticipant).filter(
        CallParticipant.user_id == user_id,
        Call.status == CallStatus.completed,
        Call.satisfaction_score.isnot(None)
    ).scalar() or 0
    
    return {
        "total_calls": total_calls,
        "upcoming_calls": upcoming,
        "completed_calls": completed,
        "cancelled_calls": cancelled,
        "total_participants": int(total_participants),
        "average_duration_minutes": round(float(avg_duration), 2),
        "average_attendance_rate": round(float(avg_attendance), 2),
        "average_satisfaction": round(float(avg_satisfaction), 2),
        "most_popular_time_slot": "14:00-15:00",  # TODO: Calculer vraiment
        "busiest_day_of_week": "Mardi"  # TODO: Calculer vraiment
    }

def get_participant_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
    """Statistiques de participation"""
    
    participations = db.query(CallParticipant).options(
        joinedload(CallParticipant.call)
    ).filter(CallParticipant.user_id == user_id).all()
    
    total_calls = len(participations)
    attended_calls = len([p for p in participations if p.status == ParticipantStatus.attended])
    hosted_calls = len([p for p in participations if p.role == ParticipantRole.host])
    no_shows = len([p for p in participations if p.status == ParticipantStatus.no_show])
    
    # Temps total passé
    total_minutes = sum(p.actual_duration_minutes or 0 for p in participations)
    total_hours = total_minutes / 60
    
    # Score d'engagement moyen
    engagement_scores = [p.engagement_score for p in participations if p.engagement_score > 0]
    avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
    
    # Satisfaction donnée
    satisfaction_ratings = [p.satisfaction_rating for p in participations if p.satisfaction_rating]
    avg_satisfaction_given = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0
    
    # Taux de no-show
    no_show_rate = (no_shows / total_calls * 100) if total_calls > 0 else 0
    
    return {
        "total_calls_attended": attended_calls,
        "total_hours_spent": round(total_hours, 2),
        "average_engagement_score": round(avg_engagement, 2),
        "calls_hosted": hosted_calls,
        "calls_as_participant": total_calls - hosted_calls,
        "no_show_rate": round(no_show_rate, 2),
        "average_satisfaction_given": round(avg_satisfaction_given, 2)
    }