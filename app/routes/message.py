from mailbox import Message
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import time

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import (
    MessageCreate, MessageResponse, MessageUpdate, MessageSearchFilters,
    MessageSearchResult, MessageStats, ConversationResponse, MessageThread,
    MessageReactionCreate, MessageReactionResponse, MessageAttachmentResponse,
    ConversationSummary, TypingIndicator, MessageDeliveryStatus
)
from app.crud.message import (
    create_message, get_message_by_id, get_conversation_messages,
    get_user_conversations, mark_message_as_read, mark_conversation_as_read,
    update_message, soft_delete_message, search_messages, add_reaction,
    remove_reaction, add_message_attachment, get_message_stats
)
from app.crud.user import get_user_by_id
from app.crud.program import get_program
from app.utils.supabase_storage import storage, get_content_type

router = APIRouter(prefix="/messages", tags=["Messages"])

def format_message_response(message, current_user_id: UUID) -> dict:
    """Formater un message pour la réponse API"""
    sender = message.sender
    receiver = message.receiver
    
    # Formater attachments
    attachments = []
    for att in message.attachments:
        attachments.append({
            "attachment_id": att.attachment_id,
            "message_id": att.message_id,
            "file_name": att.file_name,
            "original_file_name": att.original_file_name,
            "file_url": att.file_url,
            "file_size": att.file_size,
            "content_type": att.content_type,
            "file_extension": att.file_extension,
            "image_width": att.image_width,
            "image_height": att.image_height,
            "uploaded_at": att.uploaded_at,
            "is_image": att.is_image,
            "file_size_mb": att.file_size_mb
        })
    
    # Formater réactions
    reactions = []
    for react in message.reactions:
        reactions.append({
            "reaction_id": react.reaction_id,
            "message_id": react.message_id,
            "user_id": react.user_id,
            "user_name": f"{react.user.first_name} {react.user.last_name}" if react.user else "Utilisateur",
            "emoji": react.emoji,
            "reaction_type": react.reaction_type,
            "created_at": react.created_at
        })
    
    # Compter réponses
    reply_count = len(message.replies) if hasattr(message, 'replies') else 0
    
    return {
        "message_id": message.message_id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "sender_name": f"{sender.first_name} {sender.last_name}" if sender else "Système",
        "receiver_name": f"{receiver.first_name} {receiver.last_name}" if receiver else None,
        "subject": message.subject,
        "message_text": message.message_text,
        "message_type": message.message_type,
        "priority": message.priority,
        "program_id": message.program_id,
        "program_name": message.program.name if message.program else None,
        "status": message.status,
        "is_read": message.is_read,
        "is_starred": message.is_starred,
        "is_archived": message.is_archived,
        "is_deleted_by_sender": message.is_deleted_by_sender,
        "is_deleted_by_receiver": message.is_deleted_by_receiver,
        "sent_at": message.sent_at,
        "delivered_at": message.delivered_at,
        "read_at": message.read_at,
        "expires_at": message.expires_at,
        "last_edited_at": message.last_edited_at,
        "conversation_id": message.conversation_id,
        "parent_message_id": message.parent_message_id,
        "edit_count": message.edit_count,
        "attachments": attachments,
        "reactions": reactions,
        "reply_count": reply_count,
        "is_group_message": message.is_group_message,
        "conversation_identifier": message.conversation_identifier
    }

# ========== ENVOI ET GESTION DES MESSAGES ==========

@router.post("/", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📤 Envoyer un message"""
    
    # Vérifications de base
    if message_data.receiver_id:
        receiver = get_user_by_id(db, message_data.receiver_id)
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destinataire non trouvé"
            )
    
    if message_data.program_id:
        program = get_program(db, message_data.program_id)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programme non trouvé"
            )
    
    # Vérifier message parent si c'est une réponse
    if message_data.parent_message_id:
        parent = get_message_by_id(db, message_data.parent_message_id, current_user.user_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message parent non trouvé"
            )
    
    # Créer message
    message = create_message(
        db, 
        message_data, 
        current_user.user_id,
        ip_address="127.0.0.1",  # TODO: Récupérer vraie IP
        user_agent="FastAPI Client"  # TODO: Récupérer vrai user agent
    )
    
    # TODO: Envoyer notification push/email
    # TODO: Envoyer via WebSocket pour temps réel
    
    return MessageResponse(**format_message_response(message, current_user.user_id))

@router.post("/with-attachment")
async def send_message_with_attachment(
    receiver_id: Optional[UUID] = Form(None),
    program_id: Optional[UUID] = Form(None),
    subject: Optional[str] = Form(None),
    message_text: str = Form(...),
    priority: str = Form("normal"),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📎 Envoyer message avec pièces jointes"""
    
    # Validations
    if not receiver_id and not program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destinataire ou programme requis"
        )
    
    # Limiter nombre et taille des fichiers
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 fichiers par message"
        )
    
    total_size = sum(file.size for file in files)
    if total_size > 50 * 1024 * 1024:  # 50MB max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Taille totale des fichiers limitée à 50MB"
        )
    
    # Créer message
    message_data = MessageCreate(
        receiver_id=receiver_id,
        program_id=program_id,
        subject=subject,
        message_text=message_text,
        priority=priority
    )
    
    message = create_message(db, message_data, current_user.user_id)
    
    # Upload et attacher fichiers
    uploaded_files = []
    for file in files:
        try:
            file_content = await file.read()
            content_type = get_content_type(file.filename)
            
            # Upload vers Supabase
            upload_result = storage.upload_file(
                bucket_name="documents",
                file_content=file_content,
                file_name=file.filename,
                content_type=content_type,
                folder=f"messages/{current_user.user_id}"
            )
            
            if upload_result['success']:
                # Créer attachment en DB
                file_data = {
                    "file_name": upload_result['path'].split('/')[-1],
                    "original_file_name": file.filename,
                    "file_url": upload_result['url'],
                    "file_path": upload_result['path'],
                    "file_size": file.size,
                    "content_type": content_type,
                    "file_extension": file.filename.split('.')[-1] if '.' in file.filename else None
                }
                
                attachment = add_message_attachment(db, message.message_id, file_data)
                uploaded_files.append(attachment)
                
        except Exception as e:
            # Log erreur mais continue avec autres fichiers
            print(f"Erreur upload {file.filename}: {e}")
    
    # Rafraîchir message avec attachments
    db.refresh(message)
    
    return MessageResponse(**format_message_response(message, current_user.user_id))

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Récupérer un message"""
    
    message = get_message_by_id(db, message_id, current_user.user_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    # Marquer comme lu si c'est le destinataire
    if message.receiver_id == current_user.user_id and not message.is_read:
        mark_message_as_read(db, message_id, current_user.user_id)
        db.refresh(message)
    
    return MessageResponse(**format_message_response(message, current_user.user_id))

@router.put("/{message_id}", response_model=MessageResponse)
def update_my_message(
    message_id: UUID,
    update_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ Modifier mon message"""
    
    message = update_message(db, message_id, current_user.user_id, update_data)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé ou non autorisé"
        )
    
    return MessageResponse(**format_message_response(message, current_user.user_id))

@router.delete("/{message_id}")
def delete_my_message(
    message_id: UUID,
    delete_for_all: bool = Query(False, description="Supprimer pour tous"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer mon message"""
    
    success = soft_delete_message(db, message_id, current_user.user_id, delete_for_all)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé ou non autorisé"
        )
    
    return {"message": "Message supprimé avec succès"}

# ========== CONVERSATIONS ==========

@router.get("/conversations/", response_model=List[ConversationResponse])
def get_my_conversations(
    include_archived: bool = Query(False, description="Inclure conversations archivées"),
    limit: int = Query(20, description="Nombre de conversations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """💬 Mes conversations"""
    
    conversations_data = get_user_conversations(db, current_user.user_id, limit, include_archived)
    
    result = []
    for conv_data in conversations_data:
        conv = conv_data["conversation"]
        last_message = conv_data["last_message"]
        unread_count = conv_data["unread_count"]
        
        # Récupérer participants
        participants = []
        for participant_id in conv.participant_ids:
            if participant_id != current_user.user_id:  # Exclure utilisateur actuel
                user = get_user_by_id(db, participant_id)
                if user:
                    participants.append({
                        "user_id": user.user_id,
                        "name": f"{user.first_name} {user.last_name}",
                        "user_type": user.user_type.value,
                        "avatar_url": None,  # TODO: Implémenter avatars
                        "is_online": False,  # TODO: Implémenter statut online
                        "last_seen": None
                    })
        
        result.append(ConversationResponse(
            conversation_id=conv.conversation_id,
            conversation_key=conv.conversation_key,
            title=conv.title,
            conversation_type=conv.conversation_type,
            participants=participants,
            participant_count=conv.participant_count,
            message_count=conv.message_count,
            unread_count=unread_count,
            last_message=MessageResponse(**format_message_response(last_message, current_user.user_id)) if last_message else None,
            last_activity_at=conv.last_activity_at,
            is_muted=conv.is_muted,
            is_active=conv.is_active
        ))
    
    return result

@router.get("/conversations/{conversation_id}", response_model=List[MessageResponse])
def get_conversation_messages_route(
    conversation_id: str,
    skip: int = Query(0, description="Messages à ignorer"),
    limit: int = Query(50, description="Nombre de messages"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📜 Messages d'une conversation"""
    
    messages = get_conversation_messages(db, conversation_id, current_user.user_id, skip, limit)
    
    # Marquer conversation comme lue
    mark_conversation_as_read(db, conversation_id, current_user.user_id)
    
    return [
        MessageResponse(**format_message_response(msg, current_user.user_id))
        for msg in reversed(messages)  # Ordre chronologique
    ]

@router.put("/conversations/{conversation_id}/read")
def mark_conversation_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✅ Marquer conversation comme lue"""
    
    count = mark_conversation_as_read(db, conversation_id, current_user.user_id)
    
    return {"message": f"{count} messages marqués comme lus"}

# ========== RÉACTIONS ==========

@router.post("/{message_id}/reactions", response_model=MessageReactionResponse)
def add_message_reaction(
    message_id: UUID,
    reaction_data: MessageReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """👍 Ajouter réaction à un message"""
    
    reaction = add_reaction(
        db, message_id, current_user.user_id, 
        reaction_data.emoji, reaction_data.reaction_type
    )
    
    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    return MessageReactionResponse(
        reaction_id=reaction.reaction_id,
        message_id=reaction.message_id,
        user_id=reaction.user_id,
        user_name=f"{current_user.first_name} {current_user.last_name}",
        emoji=reaction.emoji,
        reaction_type=reaction.reaction_type,
        created_at=reaction.created_at
    )

@router.delete("/{message_id}/reactions")
def remove_message_reaction(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """❌ Supprimer ma réaction"""
    
    success = remove_reaction(db, message_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réaction non trouvée"
        )
    
    return {"message": "Réaction supprimée"}

# ========== RECHERCHE ==========

@router.post("/search", response_model=MessageSearchResult)
def search_my_messages(
    filters: MessageSearchFilters,
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 Rechercher dans mes messages"""
    
    start_time = time.time()
    
    messages, total_count = search_messages(db, current_user.user_id, filters, skip, limit)
    
    search_time_ms = (time.time() - start_time) * 1000
    
    # Identifier conversations trouvées
    conversation_ids = set(msg.conversation_id for msg in messages if msg.conversation_id)
    conversations_found = []
    
    for conv_id in conversation_ids:
        conv_data = get_user_conversations(db, current_user.user_id, limit=100)
        for conv in conv_data:
            if conv["conversation"].conversation_key == conv_id:
                conversations_found.append(conv["conversation"])
                break
    
    return MessageSearchResult(
        messages=[MessageResponse(**format_message_response(msg, current_user.user_id)) for msg in messages],
        total_count=total_count,
        conversations_found=[],  # Simplifier pour l'instant
        search_time_ms=round(search_time_ms, 2)
    )

# ========== STATISTIQUES ==========

@router.get("/stats", response_model=MessageStats)
def get_my_message_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Mes statistiques de messaging"""
    
    stats = get_message_stats(db, current_user.user_id)
    return MessageStats(**stats)

@router.get("/unread-count")
def get_unread_messages_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔔 Nombre de messages non lus"""
    
    from app.crud.message import get_unread_messages_count
    count = get_unread_messages_count(db, current_user.user_id)
    
    return {"unread_count": count}

@router.get("/summary", response_model=ConversationSummary)
def get_messaging_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Résumé de mes messages"""
    
    # Récupérer conversations actives (limitées)
    conversations_data = get_user_conversations(db, current_user.user_id, limit=5)
    
    active_conversations = []
    for conv_data in conversations_data:
        conv = conv_data["conversation"]
        last_message = conv_data["last_message"]
        unread_count = conv_data["unread_count"]
        
        # Participants simplifiés
        participants = []
        for participant_id in conv.participant_ids[:3]:  # Max 3 participants affichés
            if participant_id != current_user.user_id:
                user = get_user_by_id(db, participant_id)
                if user:
                    participants.append({
                        "user_id": user.user_id,
                        "name": f"{user.first_name} {user.last_name}",
                        "user_type": user.user_type.value,
                        "avatar_url": None,
                        "is_online": False,
                        "last_seen": None
                    })
        
        active_conversations.append(ConversationResponse(
            conversation_id=conv.conversation_id,
            conversation_key=conv.conversation_key,
            title=conv.title,
            conversation_type=conv.conversation_type,
            participants=participants,
            participant_count=conv.participant_count,
            message_count=conv.message_count,
            unread_count=unread_count,
            last_message=MessageResponse(**format_message_response(last_message, current_user.user_id)) if last_message else None,
            last_activity_at=conv.last_activity_at,
            is_muted=conv.is_muted,
            is_active=conv.is_active
        ))
    
    # Messages récents
    from app.crud.message import get_user_recent_messages
    recent_messages_data = get_user_recent_messages(db, current_user.user_id, 5)
    recent_messages = [
        MessageResponse(**format_message_response(msg, current_user.user_id))
        for msg in recent_messages_data
    ]
    
    # Stats
    from app.crud.message import get_unread_messages_count
    unread_count = get_unread_messages_count(db, current_user.user_id)
    
    return ConversationSummary(
        total_conversations=len(conversations_data),
        unread_messages=unread_count,
        active_conversations=active_conversations,
        recent_messages=recent_messages
    )

# ========== THREADS (FILS DE DISCUSSION) ==========

@router.get("/{message_id}/thread", response_model=MessageThread)
def get_message_thread(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🧵 Récupérer fil de discussion"""
    
    # Récupérer message parent
    parent_message = get_message_by_id(db, message_id, current_user.user_id)
    
    if not parent_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    # Si c'est une réponse, récupérer le vrai parent
    if parent_message.parent_message_id:
        actual_parent = get_message_by_id(db, parent_message.parent_message_id, current_user.user_id)
        if actual_parent:
            parent_message = actual_parent
    
    # Récupérer toutes les réponses
    from sqlalchemy import and_
    replies = db.query(Message).filter(
        Message.parent_message_id == parent_message.message_id,
        or_(
            Message.sender_id == current_user.user_id,
            Message.receiver_id == current_user.user_id
        )
    ).order_by(Message.sent_at).all()
    
    # Participants du thread
    participant_ids = {parent_message.sender_id}
    if parent_message.receiver_id:
        participant_ids.add(parent_message.receiver_id)
    
    for reply in replies:
        participant_ids.add(reply.sender_id)
        if reply.receiver_id:
            participant_ids.add(reply.receiver_id)
    
    participants = []
    for pid in participant_ids:
        user = get_user_by_id(db, pid)
        if user:
            participants.append({
                "user_id": user.user_id,
                "name": f"{user.first_name} {user.last_name}",
                "user_type": user.user_type.value,
                "avatar_url": None,
                "is_online": False,
                "last_seen": None
            })
    
    return MessageThread(
        parent_message=MessageResponse(**format_message_response(parent_message, current_user.user_id)),
        replies=[MessageResponse(**format_message_response(reply, current_user.user_id)) for reply in replies],
        total_replies=len(replies),
        participants=participants
    )

# ========== UTILITAIRES ==========

@router.post("/mark-delivered/{message_id}")
def mark_message_delivered(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📬 Marquer message comme livré (pour notifications push)"""
    
    message = get_message_by_id(db, message_id, current_user.user_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    if message.receiver_id == current_user.user_id:
        message.delivered_at = datetime.utcnow()
        if message.status == "sent":
            message.status = "delivered"
        db.commit()
    
    return {"message": "Message marqué comme livré"}