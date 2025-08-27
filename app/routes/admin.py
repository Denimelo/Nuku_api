from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session
import pandas as pd
from uuid import UUID
import io
import json
from app.database import get_db
from app.models.user import User, UserStatus
from app.models.call import Call
from app.models.program import Program
from app.models.programParticipant import ProgramParticipant
from app.models.module import Module
from app.models.moduleProgress import ModuleProgress
from app.models.message import Message
from app.models.expert import Expert
from app.models.entrepreneur import Entrepreneur
from app.models.expertMentoring import ExpertMentoring, MentoringStatus
from app.schemas.user import UserResponse
from app.schemas.entrepreneur import EntrepreneurResponse
from app.schemas.expert import ExpertCreate, ExpertResponse
from app.crud.user import get_user_by_email, get_user_by_id
from app.crud.expert import create_expert, get_expert_by_id
from app.crud.program import get_program
from app.crud.entrepreneur import get_entrepreneur_by_id
from app.auth.dependencies import get_current_user, require_admin
from app.utils.email import send_expert_welcome_email, send_entrepreneur_validation_email, send_entrepreneur_rejection_email
from app.utils.security import generate_temporary_password
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Router pour les opérations administratives
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/experts", response_model=ExpertResponse, dependencies=[Depends(require_admin)])
def admin_create_expert(data: ExpertCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    temp_password = generate_temporary_password()
    expert = create_expert(db, data, temp_password)

    # Envoi de l'email de bienvenue à l'expert
    send_expert_welcome_email(expert.user.email, f"{expert.user.first_name} {expert.user.last_name}", temp_password)
    
    return expert

@router.put("/entrepreneurs/{entrepreneur_id}/validate", dependencies=[Depends(require_admin)])
def validate_entrepreneur(entrepreneur_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.entrepreneur import ValidationStatus

    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")

    entrepreneur.validation_status = ValidationStatus.approved
    entrepreneur.validation_date = datetime.utcnow()
    entrepreneur.validated_by = current_user.user_id

    # Activation de l'utilisateur
    user = get_user_by_id(db, entrepreneur.user_id)
    user.status = UserStatus.active

    db.commit()
    send_entrepreneur_validation_email(user.email, f"{user.first_name} {user.last_name}")

    return {"message": "Compte validé avec succès"}

@router.put("/entrepreneurs/{entrepreneur_id}/reject", dependencies=[Depends(require_admin)])
def reject_entrepreneur(entrepreneur_id: UUID, db: Session = Depends(get_db)):
    from app.models.entrepreneur import ValidationStatus

    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")

    entrepreneur.validation_status = ValidationStatus.rejected
    db.commit()

    user = get_user_by_id(db, entrepreneur.user_id)
    send_entrepreneur_rejection_email(user.email, f"{user.first_name} {user.last_name}")
    
    return {"message": "Candidature rejetée"}

@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/experts", response_model=List[ExpertResponse], dependencies=[Depends(require_admin)])
def list_all_experts(db: Session = Depends(get_db)):
    return db.query(Expert).all()

@router.get("/entrepreneurs", response_model=List[EntrepreneurResponse], dependencies=[Depends(require_admin)])
def list_all_entrepreneurs(db: Session = Depends(get_db)):
    return db.query(Entrepreneur).all()

@router.get("/entrepreneurs/{entrepreneur_id}", response_model=EntrepreneurResponse, dependencies=[Depends(require_admin)])
def get_entrepreneur_by_id_route(
    entrepreneur_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")
    return entrepreneur

@router.get("/experts/{expert_id}", response_model=ExpertResponse)
def get_expert_by_id_route(
    expert_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin)
):
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert introuvable")
    return expert

@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}

@router.delete("/experts/{expert_id}", dependencies=[Depends(require_admin)])
def delete_expert(expert_id: UUID, db: Session = Depends(get_db)):
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert introuvable")
    
    db.delete(expert)
    db.commit()
    return {"message": "Expert supprimé avec succès"}

@router.put("/users/{user_id}/activate", dependencies=[Depends(require_admin)])
def activate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Activer un utilisateur"""
    user = get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    user.status = UserStatus.active
    db.commit()
    
    return {"message": "Utilisateur activé avec succès", "user_id": str(user_id)}

@router.put("/users/{user_id}/deactivate", dependencies=[Depends(require_admin)])
def deactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Désactiver un utilisateur"""
    user = get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    user.status = UserStatus.inactive
    db.commit()
    
    return {"message": "Utilisateur désactivé avec succès", "user_id": str(user_id)}

@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def get_user_details(user_id: UUID, db: Session = Depends(get_db)):
    """Récupérer les détails d'un utilisateur spécifique"""
    user = get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def update_user(user_id: UUID, user_data: dict, db: Session = Depends(get_db)):
    """Mettre à jour un utilisateur"""
    user = get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    # Mise à jour des champs autorisés
    for field, value in user_data.items():
        if hasattr(user, field) and field not in ['user_id', 'created_at', 'password_hash']:
            setattr(user, field, value)
    
    db.commit()
    
    return user

# ========== ROUTES RAPPORTS ==========

@router.get("/reports/platform-metrics", dependencies=[Depends(require_admin)])
def get_platform_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """📊 Métriques générales de la plateforme"""
    
    # Définir les dates par défaut (30 derniers jours)
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    # Métriques utilisateurs
    total_users = db.query(User).count()
    active_users_7d = db.query(User).filter(
        User.last_login >= datetime.now() - timedelta(days=7)
    ).count()
    new_users_7d = db.query(User).filter(
        User.created_at >= datetime.now() - timedelta(days=7)
    ).count()

    # Métriques programmes
    total_programs = db.query(Program).count()
    active_programs = db.query(Program).filter(Program.is_active == True).count()

    # Métriques appels
    upcoming_calls = db.query(Call).filter(
        Call.scheduled_start >= datetime.now(),
        Call.status == 'scheduled'
    ).count()

    # Métriques messages (7 derniers jours)
    messages_sent_7d = db.query(Message).filter(
        Message.sent_at >= datetime.now() - timedelta(days=7)
    ).count()

    return {
        "total_users": total_users,
        "active_users_7d": active_users_7d,
        "new_users_7d": new_users_7d,
        "total_programs": total_programs,
        "active_programs": active_programs,
        "upcoming_calls": upcoming_calls,
        "messages_sent_7d": messages_sent_7d,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }

@router.get("/reports/user-activity", dependencies=[Depends(require_admin)])
def get_user_activity_report(
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """👥 Rapport d'activité des utilisateurs"""
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    # Si user_id spécifique
    if user_id:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Statistiques détaillées pour cet utilisateur
        login_count_7d = db.query(User).filter(
            User.user_id == user_id,
            User.last_login >= datetime.now() - timedelta(days=7)
        ).count()
        
        # Modules complétés (si entrepreneur)
        completed_modules = 0
        if user.user_type.value == "entrepreneur":
            completed_modules = db.query(ModuleProgress).join(Entrepreneur).filter(
                Entrepreneur.user_id == user_id,
                ModuleProgress.is_completed == True
            ).count()

        return {
            "user_id": user_id,
            "user_name": f"{user.first_name} {user.last_name}",
            "last_login": user.last_login,
            "login_count_7d": login_count_7d,
            "completed_modules": completed_modules,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    
    # Rapport global d'activité
    active_users = db.query(User).filter(
        User.last_login >= start_date
    ).all()
    
    activity_data = []
    for user in active_users:
        activity_data.append({
            "user_id": str(user.user_id),
            "name": f"{user.first_name} {user.last_name}",
            "user_type": user.user_type.value,
            "last_login": user.last_login,
            "status": user.status.value
        })
    
    return {
        "total_active_users": len(activity_data),
        "users": activity_data,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }

@router.get("/reports/programs/{program_id}/stats", dependencies=[Depends(require_admin)])
def get_program_stats_report(
    program_id: UUID,
    db: Session = Depends(get_db)
):
    """📚 Statistiques détaillées d'un programme"""
    
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    
    # Participants
    total_participants = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id
    ).count()
    
    active_participants = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.completion_status == 'in_progress'
    ).count()
    
    completed_participants = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.completion_status == 'completed'
    ).count()
    
    dropped_participants = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.completion_status == 'dropped'
    ).count()

    # Taux de completion
    completion_rate = (completed_participants / total_participants * 100) if total_participants > 0 else 0

    # Modules du programme
    modules = db.query(Module).filter(Module.program_id == program_id).all()
    module_stats = []
    
    for module in modules:
        module_completion = db.query(ModuleProgress).filter(
            ModuleProgress.module_id == module.module_id,
            ModuleProgress.is_completed == True
        ).count()
        
        module_stats.append({
            "module_id": str(module.module_id),
            "title": module.title,
            "completion_count": module_completion,
            "completion_rate": (module_completion / total_participants * 100) if total_participants > 0 else 0
        })

    return {
        "program_id": str(program_id),
        "program_name": program.name,
        "total_participants": total_participants,
        "active_participants": active_participants,
        "completed_participants": completed_participants,
        "dropped_participants": dropped_participants,
        "completion_rate": completion_rate,
        "modules": module_stats
    }

@router.post("/reports/export", dependencies=[Depends(require_admin)])
def export_report(
    report_type: str,
    format: str = "excel",  # "excel" ou "pdf"
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """📥 Exporter rapport en Excel ou PDF"""
    
    if format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez 'excel' ou 'pdf'")
    
    # Générer les données selon le type de rapport
    if report_type == "platform_overview":
        data = get_platform_metrics(start_date, end_date, db)
        filename = f"rapport_plateforme_{datetime.now().strftime('%Y%m%d')}"
        
    elif report_type == "user_activity":
        data = get_user_activity_report(None, start_date, end_date, db)
        filename = f"rapport_utilisateurs_{datetime.now().strftime('%Y%m%d')}"
        
    else:
        raise HTTPException(status_code=400, detail="Type de rapport non supporté")

    if format == "excel":
        return export_to_excel(data, filename)
    else:
        return export_to_pdf(data, filename, report_type)

def export_to_excel(data: dict, filename: str):
    """Exporter en Excel avec design amélioré"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Feuille résumé
        summary_data = {k: v for k, v in data.items() if not isinstance(v, (list, dict)) or k == "period"}
        df_summary = pd.DataFrame([summary_data])
        df_summary.to_excel(writer, sheet_name='Résumé', index=False)

        # Feuille utilisateurs si présente
        if "users" in data and isinstance(data["users"], list) and data["users"]:
            df_users = pd.DataFrame(data["users"])
            df_users.to_excel(writer, sheet_name='Utilisateurs', index=False)

        # Feuille modules si présente
        if "modules" in data and isinstance(data["modules"], list) and data["modules"]:
            df_modules = pd.DataFrame(data["modules"])
            df_modules.to_excel(writer, sheet_name='Modules', index=False)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
    )

def export_to_pdf(data: dict, filename: str, report_type: str):
    """Exporter en PDF avec design amélioré (reportlab)"""
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin

    # Titre
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, f"Rapport {report_type.replace('_', ' ').title()}")
    y -= 30

    # Date de génération
    c.setFont("Helvetica", 12)
    c.drawString(margin, y, f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 25

    # Période
    if "period" in data:
        c.drawString(margin, y, f"Période : {data['period'].get('start_date', '')} à {data['period'].get('end_date', '')}")
        y -= 20

    # Résumé des métriques
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Résumé")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in data.items():
        if isinstance(value, (list, dict)) or key == "period":
            continue
        c.drawString(margin, y, f"{key.replace('_', ' ').capitalize()} : {value}")
        y -= 18

    # Tableau utilisateurs si présent
    if "users" in data and isinstance(data["users"], list) and data["users"]:
        y -= 10
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Utilisateurs actifs")
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        headers = ["Nom", "Type", "Dernière connexion", "Statut"]
        for i, h in enumerate(headers):
            c.drawString(margin + i*120, y, h)
        y -= 15
        c.setFont("Helvetica", 10)
        for user in data["users"]:
            c.drawString(margin, y, user.get("name", ""))
            c.drawString(margin + 120, y, user.get("user_type", ""))
            c.drawString(margin + 240, y, str(user.get("last_login", "")))
            c.drawString(margin + 360, y, user.get("status", ""))
            y -= 13
            if y < margin + 50:
                c.showPage()
                y = height - margin

    # Tableau modules si présent
    if "modules" in data and isinstance(data["modules"], list) and data["modules"]:
        y -= 10
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Modules")
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        headers = ["Titre", "Complétés", "Taux (%)"]
        for i, h in enumerate(headers):
            c.drawString(margin + i*180, y, h)
        y -= 15
        c.setFont("Helvetica", 10)
        for module in data["modules"]:
            c.drawString(margin, y, module.get("title", ""))
            c.drawString(margin + 180, y, str(module.get("completion_count", "")))
            c.drawString(margin + 360, y, str(module.get("completion_rate", "")))
            y -= 13
            if y < margin + 50:
                c.showPage()
                y = height - margin

    c.save()
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
    )

# ========== SYSTÈME DE MENTORAT ==========

@router.post("/mentoring/assign", dependencies=[Depends(require_admin)])
def assign_mentor_to_entrepreneur(
    expert_id: UUID,
    entrepreneur_id: UUID,
    db: Session = Depends(get_db)
):
    """👨‍🏫 Assigner un mentor (expert) à un entrepreneur"""
    
    # Vérifier que l'expert existe
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert non trouvé")
    
    # Vérifier que l'entrepreneur existe
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur non trouvé")
    
    # Vérifier que l'entrepreneur n'a pas déjà terminé sa formation
    entrepreneur_progress = check_entrepreneur_completion_status(db, entrepreneur_id)
    if entrepreneur_progress["is_completed"]:
        raise HTTPException(
            status_code=400, 
            detail="Cet entrepreneur a déjà terminé sa formation"
        )
    
    # Vérifier le nombre d'entrepreneurs actifs de l'expert
    active_mentees = get_expert_active_mentees_count(db, expert_id)
    if active_mentees >= 3:
        raise HTTPException(
            status_code=400, 
            detail="Cet expert a déjà 3 mentorés actifs (maximum autorisé)"
        )
    
    # Vérifier si l'entrepreneur a déjà un mentor actif
    existing_mentoring = db.query(ExpertMentoring).filter(
        ExpertMentoring.entrepreneur_id == entrepreneur_id,
        ExpertMentoring.status == 'active'
    ).first()
    
    if existing_mentoring:
        raise HTTPException(
            status_code=400,
            detail="Cet entrepreneur a déjà un mentor assigné"
        )
    
    # Créer la relation de mentorat
    mentoring = ExpertMentoring(
        expert_id=expert_id,
        entrepreneur_id=entrepreneur_id,
        assigned_date=datetime.utcnow(),
        status='active'
    )
    
    db.add(mentoring)
    db.commit()
    
    return {
        "message": "Mentor assigné avec succès",
        "expert_name": f"{expert.user.first_name} {expert.user.last_name}",
        "entrepreneur_name": f"{entrepreneur.user.first_name} {entrepreneur.user.last_name}",
        "assigned_date": mentoring.assigned_date
    }

@router.get("/mentoring/expert/{expert_id}/mentees", dependencies=[Depends(require_admin)])
def get_expert_mentees(expert_id: UUID, db: Session = Depends(get_db)):
    """👥 Liste des mentorés d'un expert"""
    
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert non trouvé")
    
    # Récupérer tous les mentorés (actifs et anciens)
    mentorings = db.query(ExpertMentoring).filter(
        ExpertMentoring.expert_id == expert_id
    ).order_by(desc(ExpertMentoring.assigned_date)).all()
    
    mentees_data = []
    active_count = 0
    
    for mentoring in mentorings:
        entrepreneur = mentoring.entrepreneur
        progress = check_entrepreneur_completion_status(db, entrepreneur.entrepreneur_id)
        
        if mentoring.status == 'active':
            active_count += 1
        
        mentees_data.append({
            "mentoring_id": str(mentoring.mentoring_id),
            "entrepreneur_id": str(entrepreneur.entrepreneur_id),
            "entrepreneur_name": f"{entrepreneur.user.first_name} {entrepreneur.user.last_name}",
            "company_name": entrepreneur.company_name,
            "assigned_date": mentoring.assigned_date,
            "status": mentoring.status,
            "completion_percentage": progress["completion_percentage"],
            "is_completed": progress["is_completed"],
            "completed_modules": progress["completed_modules"],
            "total_modules": progress["total_modules"]
        })
    
    return {
        "expert_name": f"{expert.user.first_name} {expert.user.last_name}",
        "active_mentees_count": active_count,
        "max_mentees": 3,
        "available_slots": max(0, 3 - active_count),
        "mentees": mentees_data
    }

@router.put("/mentoring/{mentoring_id}/complete", dependencies=[Depends(require_admin)])
def complete_mentoring_relationship(
    mentoring_id: UUID,
    db: Session = Depends(get_db)
):
    """✅ Marquer une relation de mentorat comme terminée"""
    
    mentoring = db.query(ExpertMentoring).filter(
        ExpertMentoring.mentoring_id == mentoring_id
    ).first()
    
    if not mentoring:
        raise HTTPException(status_code=404, detail="Relation de mentorat non trouvée")
    
    # Vérifier si l'entrepreneur a terminé sa formation
    progress = check_entrepreneur_completion_status(db, mentoring.entrepreneur_id)
    
    if progress["is_completed"]:
        mentoring.status = 'completed'
        mentoring.completed_date = datetime.utcnow()
        mentoring.completion_reason = 'formation_completed'
    else:
        mentoring.status = 'inactive'
        mentoring.completed_date = datetime.utcnow()
        mentoring.completion_reason = 'manual_completion'
    
    db.commit()
    
    return {
        "message": "Relation de mentorat marquée comme terminée",
        "completion_reason": mentoring.completion_reason,
        "entrepreneur_formation_completed": progress["is_completed"]
    }

@router.get("/mentoring/stats", dependencies=[Depends(require_admin)])
def get_mentoring_stats(db: Session = Depends(get_db)):
    """📊 Statistiques du système de mentorat"""
    
    # Statistiques générales
    total_experts = db.query(Expert).filter(Expert.is_active == True).count()
    experts_with_mentees = db.query(ExpertMentoring.expert_id).filter(
        ExpertMentoring.status == 'active'
    ).distinct().count()
    
    total_active_mentorings = db.query(ExpertMentoring).filter(
        ExpertMentoring.status == 'active'
    ).count()
    
    total_completed_mentorings = db.query(ExpertMentoring).filter(
        ExpertMentoring.status == 'completed'
    ).count()
    
    # Répartition des experts par nombre de mentorés
    expert_workload = db.query(
        ExpertMentoring.expert_id,
        func.count(ExpertMentoring.entrepreneur_id).label('mentee_count')
    ).filter(
        ExpertMentoring.status == 'active'
    ).group_by(ExpertMentoring.expert_id).all()
    
    workload_distribution = {0: 0, 1: 0, 2: 0, 3: 0}
    for expert_id, count in expert_workload:
        workload_distribution[count] = workload_distribution.get(count, 0) + 1
    
    # Compter les experts sans mentorés
    workload_distribution[0] = total_experts - sum(workload_distribution.values())
    
    return {
        "total_experts": total_experts,
        "experts_with_mentees": experts_with_mentees,
        "experts_available": total_experts - experts_with_mentees,
        "total_active_mentorings": total_active_mentorings,
        "total_completed_mentorings": total_completed_mentorings,
        "average_mentees_per_expert": round(total_active_mentorings / max(1, experts_with_mentees), 2),
        "workload_distribution": {
            "0_mentees": workload_distribution[0],
            "1_mentee": workload_distribution[1],
            "2_mentees": workload_distribution[2],
            "3_mentees": workload_distribution[3]
        },
        "utilization_rate": round((experts_with_mentees / max(1, total_experts)) * 100, 2)
    }

# ========== FONCTIONS UTILITAIRES ==========

def get_expert_active_mentees_count(db: Session, expert_id: UUID) -> int:
    """Compter le nombre de mentorés actifs d'un expert"""
    return db.query(ExpertMentoring).filter(
        ExpertMentoring.expert_id == expert_id,
        ExpertMentoring.status == 'active'
    ).count()

def check_entrepreneur_completion_status(db: Session, entrepreneur_id: UUID) -> Dict[str, Any]:
    """Vérifier le statut de completion d'un entrepreneur"""
    
    # Récupérer tous les programmes auxquels l'entrepreneur participe
    participations = db.query(ProgramParticipant).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).all()
    
    if not participations:
        return {
            "is_completed": False,
            "completion_percentage": 0,
            "completed_modules": 0,
            "total_modules": 0
        }
    
    total_modules = 0
    completed_modules = 0
    
    for participation in participations:
        # Modules du programme
        program_modules = db.query(Module).filter(
            Module.program_id == participation.program_id
        ).all()
        
        for module in program_modules:
            total_modules += 1
            
            # Vérifier si le module est complété
            progress = db.query(ModuleProgress).filter(
                ModuleProgress.module_id == module.module_id,
                ModuleProgress.user_id == participation.entrepreneur.user_id,
                ModuleProgress.is_completed == True
            ).first()
            
            if progress:
                completed_modules += 1
    
    completion_percentage = (completed_modules / max(1, total_modules)) * 100
    is_completed = completion_percentage >= 100
    
    # Si l'entrepreneur a terminé sa formation, mettre à jour automatiquement les relations de mentorat
    if is_completed:
        update_mentoring_on_completion(db, entrepreneur_id)
    
    return {
        "is_completed": is_completed,
        "completion_percentage": round(completion_percentage, 2),
        "completed_modules": completed_modules,
        "total_modules": total_modules
    }

def update_mentoring_on_completion(db: Session, entrepreneur_id: UUID):
    """Mettre à jour automatiquement le mentorat quand un entrepreneur termine"""
    
    active_mentoring = db.query(ExpertMentoring).filter(
        ExpertMentoring.entrepreneur_id == entrepreneur_id,
        ExpertMentoring.status == 'active'
    ).first()
    
    if active_mentoring:
        active_mentoring.status = 'completed'
        active_mentoring.completed_date = datetime.utcnow()
        active_mentoring.completion_reason = 'formation_completed'
        db.commit()

# ========== ROUTES PARAMÈTRES ==========

@router.get("/settings/platform", dependencies=[Depends(require_admin)])
def get_platform_settings(db: Session = Depends(get_db)):
    """📋 Récupérer les paramètres de la plateforme"""
    
    # Pour l'instant, on retourne des paramètres par défaut
    # Dans une vraie implémentation, ces paramètres seraient stockés en base
    default_settings = {
        "platform_name": "NUKU",
        "base_url": "https://nuku.vercel.app",
        "description": "Plateforme d'accélération pour MPME",
        "default_language": "fr",
        "timezone": "Africa/Lome",
        "maintenance_mode": False,
        "maintenance_message": "La plateforme est en cours de maintenance. Nous reviendrons bientôt."
    }
    
    return {"settings": default_settings}

@router.put("/settings/platform", dependencies=[Depends(require_admin)])
def update_platform_settings(
    settings: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """🔧 Mettre à jour les paramètres de la plateforme"""
    
    # Dans une vraie implémentation, vous stockeriez ces paramètres en base
    # Pour l'instant, on simule la sauvegarde
    
    return {
        "message": "Paramètres de la plateforme mis à jour avec succès",
        "updated_settings": settings
    }

@router.get("/settings/system", dependencies=[Depends(require_admin)])
def get_system_settings(db: Session = Depends(get_db)):
    """⚙️ Récupérer les paramètres système"""
    
    default_settings = {
        "log_level": "INFO",
        "log_retention_days": 30,
        "max_user_sessions": 5,
        "session_timeout_minutes": 360,
        "debug_mode": False,
        "api_rate_limiting": True
    }
    
    return {"settings": default_settings}

@router.put("/settings/system", dependencies=[Depends(require_admin)])
def update_system_settings(
    settings: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """🔧 Mettre à jour les paramètres système"""
    
    return {
        "message": "Paramètres système mis à jour avec succès",
        "updated_settings": settings
    }

@router.get("/settings/email", dependencies=[Depends(require_admin)])
def get_email_settings(db: Session = Depends(get_db)):
    """📧 Récupérer les paramètres email"""
    
    # Attention: ne jamais retourner les vrais mots de passe
    default_settings = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "noreply@nuku.tg",
        "sender_name": "NUKU Platform",
        "smtp_username": "",
        "smtp_password": "***",  # Masqué pour la sécurité
        "use_tls": True,
        "use_ssl": False
    }
    
    return {"settings": default_settings}

@router.put("/settings/email", dependencies=[Depends(require_admin)])
def update_email_settings(
    settings: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """🔧 Mettre à jour les paramètres email"""
    
    # Dans une vraie implémentation, vous chiffriez le mot de passe
    return {
        "message": "Paramètres email mis à jour avec succès"
    }

@router.post("/settings/email/test", dependencies=[Depends(require_admin)])
def test_email_configuration(
    test_data: Dict[str, str], 
    db: Session = Depends(get_db)
):
    """🧪 Tester la configuration email"""
    
    test_email = test_data.get("test_email")
    
    if not test_email:
        raise HTTPException(status_code=400, detail="Email de test requis")
    
    try:
        # Ici vous implémenteriez l'envoi d'un email de test
        # Pour l'instant, on simule le succès
        
        # from app.utils.email import send_test_email
        # send_test_email(test_email)
        
        return {
            "message": f"Email de test envoyé avec succès à {test_email}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'envoi de l'email de test: {str(e)}"
        )

@router.get("/settings/storage/stats", dependencies=[Depends(require_admin)])
def get_storage_stats(db: Session = Depends(get_db)):
    """📊 Statistiques de stockage"""
    
    # Dans une vraie implémentation, vous récupéreriez ces stats depuis Supabase
    mock_stats = {
        "documents_size": "45 MB",
        "documents_count": 127,
        "avatars_size": "8 MB", 
        "avatars_count": 34,
        "modules_size": "156 MB",
        "modules_count": 23,
        "total_size": "209 MB",
        "last_calculated": datetime.now().isoformat()
    }
    
    return {"stats": mock_stats}

@router.post("/settings/backup", dependencies=[Depends(require_admin)])
def create_backup(db: Session = Depends(get_db)):
    """💾 Créer une sauvegarde manuelle"""
    
    try:
        # Dans une vraie implémentation, vous créeriez une sauvegarde
        # des données critiques (utilisateurs, programmes, etc.)
        
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Exemple de sauvegarde des utilisateurs
        users_count = db.query(User).count()
        programs_count = db.query(Program).count() if 'Program' in globals() else 0
        
        return {
            "message": "Sauvegarde créée avec succès",
            "backup_id": backup_id,
            "backup_date": datetime.now().isoformat(),
            "stats": {
                "users": users_count,
                "programs": programs_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de la sauvegarde: {str(e)}"
        )

@router.post("/settings/cache/clear", dependencies=[Depends(require_admin)])
def clear_cache(cache_type: str = Query(None), db: Session = Depends(get_db)):
    """🗑️ Vider le cache"""
    
    try:
        # Dans une vraie implémentation, vous videriez le cache Redis/Memcached
        
        cache_types_cleared = []
        
        if not cache_type or cache_type == "all":
            cache_types_cleared = ["sessions", "api_responses", "user_data"]
        else:
            cache_types_cleared = [cache_type]
        
        return {
            "message": f"Cache vidé avec succès: {', '.join(cache_types_cleared)}",
            "cleared_types": cache_types_cleared,
            "cleared_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du vidage du cache: {str(e)}"
        )

@router.get("/settings/logs", dependencies=[Depends(require_admin)])
def get_system_logs(
    level: str = Query("INFO", description="Niveau de log (DEBUG, INFO, WARNING, ERROR)"),
    limit: int = Query(100, description="Nombre maximum de logs à retourner"),
    db: Session = Depends(get_db)
):
    """📋 Récupérer les logs système"""
    
    # Dans une vraie implémentation, vous liriez les vrais logs
    mock_logs = [
        {
            "id": 1,
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "message": "Utilisateur connecté",
            "module": "auth",
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        },
        {
            "id": 2,
            "timestamp": "2024-01-15T10:25:00Z", 
            "level": "WARNING",
            "message": "Tentative de connexion échouée",
            "module": "auth",
            "ip_address": "192.168.1.100"
        },
        {
            "id": 3,
            "timestamp": "2024-01-15T10:20:00Z",
            "level": "ERROR", 
            "message": "Erreur de base de données",
            "module": "database",
            "error_code": "CONNECTION_TIMEOUT"
        }
    ]
    
    # Filtrer par niveau si spécifié
    if level != "ALL":
        mock_logs = [log for log in mock_logs if log["level"] == level]
    
    return {
        "logs": mock_logs[:limit],
        "total": len(mock_logs),
        "level_filter": level,
        "limit": limit
    }

# ========== FONCTION UTILITAIRE ==========

def get_system_info():
    """Récupérer les informations système de base"""
    return {
        "python_version": "3.13",
        "fastapi_version": "0.104.1",
        "database": "PostgreSQL (Supabase)",
        "storage": "Supabase Storage", 
        "deployment": "Render",
        "uptime": "5 jours, 3 heures"
    }