from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.auth.dependencies import get_current_user, require_expert, require_entrepreneur
from app.models.user import User
from app.schemas.call import (
    CallCreate, CallUpdate, CallResponse, CallParticipantCreate, CallParticipantUpdate,
    CallParticipantResponse, CallInvitation, CallInvitationResponse, CallSchedule,
    CallCalendar, CallStats, ParticipantStats, CallFilter, CallSearchResult,
    RecurringCallCreate, CallRecordingResponse
)
from app.crud.call import (
    create_call, get_call_by_id, get_calls_by_expert, get_calls_by_entrepreneur,
    get_calls_by_program, get_upcoming_calls, update_call, cancel_call, start_call,
    end_call, invite_participants, respond_to_invitation, join_call, leave_call,
    update_participant, get_call_participants, remove_participant, search_calls,
    get_calendar_calls, get_call_stats, get_participant_stats
)
from app.crud.expert import get_expert_by_user_id
from app.crud.entrepreneur import get_entrepreneur_by_user_id
from app.models.call import CallStatus, CallType
from app.models.callParticipant import ParticipantRole, ParticipantStatus
import time

router = APIRouter(prefix="/calls", tags=["Calls"])

def format_call_response(call, current_user_id: UUID, user_participation=None) -> dict:
    """Formater réponse d'appel"""
    
    now = datetime.utcnow()
    
    return {
        "call_id": call.call_id,
        "program_id": call.program_id,
        "module_id": call.module_id,
        "expert_id": call.expert_id,
        "created_by": call.created_by,
        "title": call.title,
        "description": call.description,
        "agenda": call.agenda,
        "call_type": call.call_type,
        "priority": call.priority,
        "scheduled_start": call.scheduled_start,
        "scheduled_end": call.scheduled_end,
        "timezone": call.timezone,
        "duration_minutes": call.duration_minutes,
        "actual_start": call.actual_start,
        "actual_end": call.actual_end,
        "actual_duration_minutes": call.actual_duration_minutes,
        "meeting_url": call.meeting_url,
        "meeting_id": call.meeting_id,
        "meeting_password": call.meeting_password,
        "platform": call.platform,
        "max_participants": call.max_participants,
        "requires_approval": call.requires_approval,
        "is_recorded": call.is_recorded,
        "reminder_minutes_before": call.reminder_minutes_before,
        "status": call.status,
        "is_recurring": call.is_recurring,
        "participant_count": call.participant_count,
        "attendance_rate": call.attendance_rate,
        "satisfaction_score": call.satisfaction_score,
        "summary": call.summary,
        "next_steps": call.next_steps,
        "follow_up_date": call.follow_up_date,
        "created_at": call.created_at,
        "updated_at": call.updated_at,
        "expert_name": f"{call.expert.user.first_name} {call.expert.user.last_name}" if call.expert and call.expert.user else None,
        "program_name": call.program.name if call.program else None,
        "module_title": call.module.title if call.module else None,
        "creator_name": f"{call.created_by_user.first_name} {call.created_by_user.last_name}" if call.created_by_user else None,
        "is_upcoming": call.is_upcoming,
        "is_live": call.is_live,
        "is_past": call.is_past,
        "can_join": call.can_join,
        "time_until_start_minutes": int(call.time_until_start.total_seconds() / 60) if call.is_upcoming else None,
        "user_participation": format_participant_response(user_participation, current_user_id) if user_participation else None
    }

def format_participant_response(participant, current_user_id: UUID) -> dict:
    """Formater réponse de participant"""
    if not participant:
        return None
    
    return {
        "participant_id": participant.participant_id,
        "call_id": participant.call_id,
        "user_id": participant.user_id,
        "entrepreneur_id": participant.entrepreneur_id,
        "expert_id": participant.expert_id,
        "role": participant.role,
        "status": participant.status,
        "invited_at": participant.invited_at,
        "invited_by": participant.invited_by,
        "responded_at": participant.responded_at,
        "response_message": participant.response_message,
        "joined_at": participant.joined_at,
        "left_at": participant.left_at,
        "actual_duration_minutes": participant.actual_duration_minutes,
        "camera_enabled": participant.camera_enabled,
        "microphone_enabled": participant.microphone_enabled,
        "screen_sharing_used": participant.screen_sharing_used,
        "questions_asked": participant.questions_asked,
        "messages_sent": participant.messages_sent,
        "polls_answered": participant.polls_answered,
        "satisfaction_rating": participant.satisfaction_rating,
        "feedback": participant.feedback,
        "would_recommend": participant.would_recommend,
        "follow_up_required": participant.follow_up_required,
        "follow_up_notes": participant.follow_up_notes,
        "next_meeting_scheduled": participant.next_meeting_scheduled,
        "display_name": participant.display_name,
        "user_type": participant.user.user_type.value if participant.user else None,
        "company_name": participant.entrepreneur.company_name if participant.entrepreneur else None,
        "attended_full_session": participant.attended_full_session,
        "engagement_score": participant.engagement_score
    }

# ========== CRÉATION ET GESTION DES APPELS ==========

@router.post("/", response_model=CallResponse)
def create_new_call(
    call_data: CallCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📞 Créer un nouvel appel"""
    
    # Vérifications de base
    if call_data.scheduled_start >= call_data.scheduled_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'heure de fin doit être après l'heure de début"
        )
    
    if call_data.scheduled_start <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'appel ne peut pas être programmé dans le passé"
        )
    
    # Déterminer expert_id
    expert_id = call_data.expert_id
    if not expert_id:
        expert = get_expert_by_user_id(db, current_user.user_id)
        if expert:
            expert_id = expert.expert_id
        elif current_user.user_type.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les experts peuvent créer des appels"
            )
    
    # TODO: Vérifier disponibilité de l'expert
    # TODO: Générer URL de réunion selon la plateforme
    
    call = create_call(db, call_data, current_user.user_id, expert_id)
    
    # TODO: Envoyer invitations par email/notification
    
    return CallResponse(**format_call_response(call, current_user.user_id))

@router.get("/{call_id}", response_model=CallResponse)
def get_call_details(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Détails d'un appel"""
    
    call = get_call_by_id(db, call_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé"
        )
    
    # Vérifier permissions
    user_participant = next(
        (p for p in call.participants if p.user_id == current_user.user_id), 
        None
    )
    
    if not user_participant and current_user.user_type.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cet appel"
        )
    
    return CallResponse(**format_call_response(call, current_user.user_id, user_participant))

@router.put("/{call_id}", response_model=CallResponse)
def update_call_details(
    call_id: UUID,
    update_data: CallUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ Modifier un appel"""
    
    call = update_call(db, call_id, update_data, current_user.user_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé ou non autorisé"
        )
    
    # TODO: Notifier participants du changement
    
    return CallResponse(**format_call_response(call, current_user.user_id))

@router.delete("/{call_id}")
def cancel_call_route(
    call_id: UUID,
    reason: Optional[str] = Query(None, description="Raison de l'annulation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """❌ Annuler un appel"""
    
    call = cancel_call(db, call_id, current_user.user_id, reason)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé ou non annulable"
        )
    
    # TODO: Notifier tous les participants
    
    return {"message": "Appel annulé avec succès", "reason": reason}

@router.post("/{call_id}/start", response_model=CallResponse)
def start_call_session(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🚀 Démarrer un appel"""
    
    call = start_call(db, call_id, current_user.user_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé ou non démarrable"
        )
    
    return CallResponse(**format_call_response(call, current_user.user_id))

@router.post("/{call_id}/end", response_model=CallResponse)
def end_call_session(
    call_id: UUID,
    summary: Optional[str] = Query(None, description="Résumé de la session"),
    next_steps: Optional[str] = Query(None, description="Actions à suivre"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🏁 Terminer un appel"""
    
    call = end_call(db, call_id, current_user.user_id, summary, next_steps)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé ou non terminable"
        )
    
    return CallResponse(**format_call_response(call, current_user.user_id))

# ========== GESTION DES PARTICIPANTS ==========

@router.post("/{call_id}/invite", response_model=CallInvitationResponse)
def invite_to_call(
    call_id: UUID,
    invitation: CallInvitation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📨 Inviter participants à un appel"""
    
    invited_count, already_invited, failed = invite_participants(
        db, call_id, invitation.participant_ids, current_user.user_id
    )
    
    # TODO: Envoyer emails/notifications si demandé
    
    return CallInvitationResponse(
        invited_count=invited_count,
        already_invited_count=already_invited,
        failed_invitations=failed
    )

@router.post("/{call_id}/respond")
def respond_to_call_invitation(
    call_id: UUID,
    response_status: ParticipantStatus,
    message: Optional[str] = Query(None, description="Message de réponse"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """💬 Répondre à une invitation d'appel"""
    
    participant = respond_to_invitation(db, call_id, current_user.user_id, response_status, message)
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation non trouvée"
        )
    
    return {"message": f"Réponse enregistrée: {response_status.value}", "status": response_status.value}

@router.post("/{call_id}/join")
def join_call_session(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🎯 Rejoindre un appel"""
    
    call = get_call_by_id(db, call_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé"
        )
    
    if not call.can_join:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de rejoindre cet appel actuellement"
        )
    
    participant = join_call(db, call_id, current_user.user_id)
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vous n'êtes pas invité à cet appel"
        )
    
    return {
        "message": "Vous avez rejoint l'appel",
        "meeting_url": call.meeting_url,
        "meeting_id": call.meeting_id,
        "meeting_password": call.meeting_password
    }

@router.post("/{call_id}/leave")
def leave_call_session(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """👋 Quitter un appel"""
    
    participant = leave_call(db, call_id, current_user.user_id)
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation non trouvée"
        )
    
    return {
        "message": "Vous avez quitté l'appel",
        "duration_minutes": participant.actual_duration_minutes
    }

@router.get("/{call_id}/participants", response_model=List[CallParticipantResponse])
def get_call_participants_list(
    call_id: UUID,
    role: Optional[ParticipantRole] = Query(None, description="Filtrer par rôle"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """👥 Liste des participants d'un appel"""
    
    # Vérifier accès à l'appel
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé"
        )
    
    participants = get_call_participants(db, call_id, role)
    
    return [
        CallParticipantResponse(**format_participant_response(participant, current_user.user_id))
        for participant in participants
    ]

@router.put("/participants/{participant_id}", response_model=CallParticipantResponse)
def update_call_participant(
    participant_id: UUID,
    update_data: CallParticipantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ Mettre à jour un participant"""
    
    participant = update_participant(db, participant_id, update_data)
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant non trouvé"
        )
    
    return CallParticipantResponse(**format_participant_response(participant, current_user.user_id))

@router.delete("/{call_id}/participants/{user_id}")
def remove_call_participant(
    call_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ Retirer un participant"""
    
    success = remove_participant(db, call_id, user_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant non trouvé"
        )
    
    return {"message": "Participant retiré de l'appel"}

# ========== LISTES ET PLANNING ==========

@router.get("/upcoming", response_model=List[CallResponse])
def get_upcoming_calls_list(
    days_ahead: int = Query(7, description="Nombre de jours à venir"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📅 Mes appels à venir"""
    
    calls = get_upcoming_calls(db, current_user.user_id, days_ahead)
    
    result = []
    for call in calls:
        user_participation = next(
            (p for p in call.participants if p.user_id == current_user.user_id),
            None
        )
        result.append(CallResponse(**format_call_response(call, current_user.user_id, user_participation)))
    
    return result

@router.get("/expert/my-calls", response_model=List[CallResponse])
def get_expert_calls(
    include_past: bool = Query(True, description="Inclure appels passés"),
    limit: int = Query(50),
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📞 Mes appels (Expert)"""
    
    expert = get_expert_by_user_id(db, current_user.user_id)
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    calls = get_calls_by_expert(db, expert.expert_id, include_past, limit)
    
    return [
        CallResponse(**format_call_response(call, current_user.user_id))
        for call in calls
    ]

@router.get("/entrepreneur/my-calls", response_model=List[CallResponse])
def get_entrepreneur_calls(
    include_past: bool = Query(True, description="Inclure appels passés"),
    limit: int = Query(50),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📞 Mes appels (Entrepreneur)"""
    
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    calls = get_calls_by_entrepreneur(db, entrepreneur.entrepreneur_id, include_past, limit)
    
    result = []
    for call in calls:
        user_participation = next(
            (p for p in call.participants if p.user_id == current_user.user_id),
            None
        )
        result.append(CallResponse(**format_call_response(call, current_user.user_id, user_participation)))
    
    return result

@router.get("/program/{program_id}", response_model=List[CallResponse])
def get_program_calls(
    program_id: UUID,
    upcoming_only: bool = Query(False, description="Seulement les appels à venir"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Appels d'un programme"""
    
    calls = get_calls_by_program(db, program_id, upcoming_only)
    
    result = []
    for call in calls:
        user_participation = next(
            (p for p in call.participants if p.user_id == current_user.user_id),
            None
        )
        result.append(CallResponse(**format_call_response(call, current_user.user_id, user_participation)))
    
    return result

@router.get("/calendar/{year}/{month}", response_model=CallCalendar)
def get_calendar_view(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📅 Vue calendrier des appels"""
    
    # Validation
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mois invalide"
        )
    
    calendar_data = get_calendar_calls(db, current_user.user_id, year, month)
    
    # Construire vue calendrier
    import calendar
    cal = calendar.monthrange(year, month)
    days_in_month = cal[1]
    
    days = []
    total_calls = 0
    
    for day in range(1, days_in_month + 1):
        day_calls = calendar_data.get(day, [])
        calls_count = len(day_calls)
        total_calls += calls_count
        
        # Vérifier conflits (plusieurs appels en même temps)
        has_conflicts = False
        if len(day_calls) > 1:
            times = [(call.scheduled_start, call.scheduled_end) for call in day_calls]
            for i, (start1, end1) in enumerate(times):
                for start2, end2 in times[i+1:]:
                    if start1 < end2 and start2 < end1:  # Overlap
                        has_conflicts = True
                        break
                if has_conflicts:
                    break
        
        days.append({
            "date": day,
            "calls_count": calls_count,
            "has_conflicts": has_conflicts
        })
    
    return CallCalendar(
        year=year,
        month=month,
        days=days,
        total_calls=total_calls
    )

# ========== RECHERCHE ==========

@router.post("/search", response_model=CallSearchResult)
def search_calls_route(
    filters: CallFilter,
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 Rechercher appels"""
    
    start_time = time.time()
    
    calls, total_count = search_calls(db, current_user.user_id, filters, skip, limit)
    
    search_time_ms = (time.time() - start_time) * 1000
    
    result_calls = []
    for call in calls:
        user_participation = next(
            (p for p in call.participants if p.user_id == current_user.user_id),
            None
        )
        result_calls.append(CallResponse(**format_call_response(call, current_user.user_id, user_participation)))
    
    return CallSearchResult(
        calls=result_calls,
        total_count=total_count,
        search_time_ms=round(search_time_ms, 2)
    )

# ========== STATISTIQUES ==========

@router.get("/stats", response_model=CallStats)
def get_call_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Mes statistiques d'appels"""
    
    stats = get_call_stats(db, current_user.user_id)
    return CallStats(**stats)

@router.get("/participant-stats", response_model=ParticipantStats)
def get_participation_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📈 Mes statistiques de participation"""
    
    stats = get_participant_stats(db, current_user.user_id)
    return ParticipantStats(**stats)

# ========== UTILITAIRES ==========

@router.get("/types")
def get_call_types():
    """📋 Types d'appels disponibles"""
    
    return {
        "call_types": [
            {
                "value": type.value,
                "label": _get_type_label(type.value),
                "description": _get_type_description(type.value)
            } for type in CallType
        ]
    }

@router.get("/platforms")
def get_supported_platforms():
    """🔗 Plateformes de visioconférence supportées"""
    
    return {
        "platforms": [
            {"value": "zoom", "label": "Zoom", "icon": "zoom"},
            {"value": "teams", "label": "Microsoft Teams", "icon": "teams"},
            {"value": "meet", "label": "Google Meet", "icon": "meet"},
            {"value": "jitsi", "label": "Jitsi Meet", "icon": "jitsi"},
            {"value": "custom", "label": "Lien personnalisé", "icon": "link"}
        ]
    }

@router.get("/{call_id}/meeting-info")
def get_meeting_info(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔗 Informations de connexion à la réunion"""
    
    call = get_call_by_id(db, call_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appel non trouvé"
        )
    
    # Vérifier que l'utilisateur est participant
    user_participant = next(
        (p for p in call.participants if p.user_id == current_user.user_id),
        None
    )
    
    if not user_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas invité à cet appel"
        )
    
    if not call.can_join:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'appel n'est pas encore accessible"
        )
    
    return {
        "call_id": call.call_id,
        "title": call.title,
        "scheduled_start": call.scheduled_start,
        "meeting_url": call.meeting_url,
        "meeting_id": call.meeting_id,
        "meeting_password": call.meeting_password,
        "platform": call.platform,
        "can_join": call.can_join,
        "time_until_start": call.time_until_start.total_seconds() if call.is_upcoming else 0
    }

def _get_type_label(call_type: str) -> str:
    """Labels des types d'appels"""
    labels = {
        "one_on_one": "Session 1:1",
        "group_session": "Session de groupe",
        "webinar": "Webinaire",
        "workshop": "Atelier",
        "office_hours": "Permanence"
    }
    return labels.get(call_type, call_type.title())

def _get_type_description(call_type: str) -> str:
    """Descriptions des types d'appels"""
    descriptions = {
        "one_on_one": "Session individuelle entrepreneur-expert",
        "group_session": "Session avec plusieurs participants d'un programme",
        "webinar": "Présentation avec un orateur principal",
        "workshop": "Atelier interactif avec exercices pratiques",
        "office_hours": "Permanence ouverte pour questions/conseils"
    }
    return descriptions.get(call_type, "Type d'appel")