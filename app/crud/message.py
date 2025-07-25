from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, asc
from uuid import UUID
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.models.message import Message, MessageType, MessageStatus, MessagePriority
from app.models.messageAttachment import MessageAttachment
from app.models.messageReaction import MessageReaction
from app.models.conversation import Conversation
from app.models.user import User
from app.models.program import Program
from app.schemas.message import MessageCreate, MessageUpdate, MessageSearchFilters

# ========== CRUD MESSAGES ==========

def create_message(
    db: Session,
    message_data: MessageCreate,
    sender_id: UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Message:
    """Créer un nouveau message avec métadonnées"""
    
    # Générer conversation_id si pas fourni
    conversation_id = None
    if message_data.receiver_id:
        conversation_id = Conversation.generate_direct_key(sender_id, message_data.receiver_id)
    elif message_data.program_id:
        conversation_id = Conversation.generate_program_key(message_data.program_id)
    
    message = Message(
        sender_id=sender_id,
        receiver_id=message_data.receiver_id,
        subject=message_data.subject,
        message_text=message_data.message_text,
        message_type=message_data.message_type,
        priority=message_data.priority,
        program_id=message_data.program_id,
        conversation_id=conversation_id,
        parent_message_id=message_data.parent_message_id,
        expires_at=message_data.expires_at,
        status=MessageStatus.sent,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(message)
    db.flush()  # Pour avoir l'ID
    
    # Créer/mettre à jour la conversation
    _update_or_create_conversation(db, message)
    
    db.commit()
    db.refresh(message)
    return message

def get_message_by_id(
    db: Session, 
    message_id: UUID, 
    user_id: UUID,
    include_deleted: bool = False
) -> Optional[Message]:
    """Récupérer message par ID avec vérifications"""
    query = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver),
        joinedload(Message.attachments),
        joinedload(Message.reactions),
        joinedload(Message.program)
    ).filter(Message.message_id == message_id)
    
    # Vérifier que l'utilisateur a accès au message
    query = query.filter(
        or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    )
    
    if not include_deleted:
        query = query.filter(
            or_(
                and_(Message.sender_id == user_id, Message.is_deleted_by_sender == False),
                and_(Message.receiver_id == user_id, Message.is_deleted_by_receiver == False)
            )
        )
    
    return query.first()

def get_conversation_messages(
    db: Session,
    conversation_id: str,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = False
) -> List[Message]:
    """Récupérer messages d'une conversation"""
    query = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver),
        joinedload(Message.attachments),
        joinedload(Message.reactions)
    ).filter(Message.conversation_id == conversation_id)
    
    # Vérifier accès utilisateur
    query = query.filter(
        or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    )
    
    if not include_deleted:
        query = query.filter(
            or_(
                and_(Message.sender_id == user_id, Message.is_deleted_by_sender == False),
                and_(Message.receiver_id == user_id, Message.is_deleted_by_receiver == False)
            )
        )
    
    return query.order_by(desc(Message.sent_at)).offset(skip).limit(limit).all()

def get_user_conversations(
    db: Session,
    user_id: UUID,
    limit: int = 20,
    include_archived: bool = False
) -> List[Dict[str, Any]]:
    """Récupérer conversations de l'utilisateur avec derniers messages"""
    
    # Récupérer toutes les conversations où l'utilisateur participe
    conversations_query = db.query(Conversation).filter(
        Conversation.participant_ids.any(user_id)
    )
    
    if not include_archived:
        conversations_query = conversations_query.filter(Conversation.is_active == True)
    
    conversations = conversations_query.order_by(desc(Conversation.last_activity_at)).limit(limit).all()
    
    result = []
    for conv in conversations:
        # Récupérer le dernier message
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.conversation_key,
            or_(
                and_(Message.sender_id == user_id, Message.is_deleted_by_sender == False),
                and_(Message.receiver_id == user_id, Message.is_deleted_by_receiver == False),
                and_(Message.receiver_id.is_(None))  # Messages de groupe
            )
        ).order_by(desc(Message.sent_at)).first()
        
        # Compter messages non lus
        unread_count = db.query(Message).filter(
            Message.conversation_id == conv.conversation_key,
            Message.receiver_id == user_id,
            Message.is_read == False,
            Message.is_deleted_by_receiver == False
        ).count()
        
        if last_message:
            result.append({
                "conversation": conv,
                "last_message": last_message,
                "unread_count": unread_count
            })
    
    return result

def mark_message_as_read(
    db: Session, 
    message_id: UUID, 
    user_id: UUID
) -> bool:
    """Marquer message comme lu"""
    message = db.query(Message).filter(
        Message.message_id == message_id,
        Message.receiver_id == user_id
    ).first()
    
    if not message or message.is_read:
        return False
    
    message.is_read = True
    message.read_at = datetime.utcnow()
    message.status = MessageStatus.read
    
    db.commit()
    return True

def mark_conversation_as_read(
    db: Session,
    conversation_id: str,
    user_id: UUID
) -> int:
    """Marquer toute une conversation comme lue"""
    unread_messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.receiver_id == user_id,
        Message.is_read == False,
        Message.is_deleted_by_receiver == False
    ).all()
    
    count = len(unread_messages)
    now = datetime.utcnow()
    
    for message in unread_messages:
        message.is_read = True
        message.read_at = now
        message.status = MessageStatus.read
    
    db.commit()
    return count

def update_message(
    db: Session,
    message_id: UUID,
    user_id: UUID,
    update_data: MessageUpdate
) -> Optional[Message]:
    """Mettre à jour un message (seul l'expéditeur peut modifier)"""
    message = db.query(Message).filter(
        Message.message_id == message_id,
        Message.sender_id == user_id
    ).first()
    
    if not message:
        return None
    
    # Mettre à jour les champs
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(message, field):
            setattr(message, field, value)
    
    # Incrémenter compteur d'édition si le texte a changé
    if update_data.message_text and update_data.message_text != message.message_text:
        message.edit_count += 1
        message.last_edited_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message

def soft_delete_message(
    db: Session,
    message_id: UUID,
    user_id: UUID,
    delete_for_all: bool = False
) -> bool:
    """Supprimer message (soft delete)"""
    message = db.query(Message).filter(Message.message_id == message_id).first()
    
    if not message:
        return False
    
    # Vérifier permissions
    if delete_for_all and message.sender_id != user_id:
        return False  # Seul l'expéditeur peut supprimer pour tous
    
    if message.sender_id == user_id:
        message.is_deleted_by_sender = True
        if delete_for_all:
            message.is_deleted_by_receiver = True
    elif message.receiver_id == user_id:
        message.is_deleted_by_receiver = True
    else:
        return False  # Utilisateur non autorisé
    
    db.commit()
    return True

def search_messages(
    db: Session,
    user_id: UUID,
    filters: MessageSearchFilters,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Message], int]:
    """Recherche avancée dans les messages"""
    query = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver),
        joinedload(Message.attachments)
    ).filter(
        or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).filter(
        or_(
            and_(Message.sender_id == user_id, Message.is_deleted_by_sender == False),
            and_(Message.receiver_id == user_id, Message.is_deleted_by_receiver == False)
        )
    )
    
    # Appliquer filtres
    if filters.query:
        query = query.filter(
            or_(
                Message.message_text.ilike(f"%{filters.query}%"),
                Message.subject.ilike(f"%{filters.query}%")
            )
        )
    
    if filters.sender_id:
        query = query.filter(Message.sender_id == filters.sender_id)
    
    if filters.conversation_id:
        query = query.filter(Message.conversation_id == filters.conversation_id)
    
    if filters.message_type:
        query = query.filter(Message.message_type == filters.message_type)
    
    if filters.has_attachments is not None:
        if filters.has_attachments:
            query = query.filter(Message.attachments.any())
        else:
            query = query.filter(~Message.attachments.any())
    
    if filters.date_from:
        query = query.filter(Message.sent_at >= filters.date_from)
    
    if filters.date_to:
        query = query.filter(Message.sent_at <= filters.date_to)
    
    if filters.is_starred is not None:
        query = query.filter(Message.is_starred == filters.is_starred)
    
    # Compter total
    total_count = query.count()
    
    # Récupérer résultats paginés
    messages = query.order_by(desc(Message.sent_at)).offset(skip).limit(limit).all()
    
    return messages, total_count

# ========== CRUD REACTIONS ==========

def add_reaction(
    db: Session,
    message_id: UUID,
    user_id: UUID,
    emoji: str,
    reaction_type: str
) -> Optional[MessageReaction]:
    """Ajouter une réaction à un message"""
    
    # Vérifier que le message existe et est accessible
    message = get_message_by_id(db, message_id, user_id)
    if not message:
        return None
    
    # Supprimer réaction existante si présente
    existing = db.query(MessageReaction).filter(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == user_id
    ).first()
    
    if existing:
        db.delete(existing)
    
    # Créer nouvelle réaction
    reaction = MessageReaction(
        message_id=message_id,
        user_id=user_id,
        emoji=emoji,
        reaction_type=reaction_type
    )
    
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction

def remove_reaction(db: Session, message_id: UUID, user_id: UUID) -> bool:
    """Supprimer réaction d'un utilisateur"""
    reaction = db.query(MessageReaction).filter(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == user_id
    ).first()
    
    if not reaction:
        return False
    
    db.delete(reaction)
    db.commit()
    return True

# ========== CRUD ATTACHMENTS ==========

def add_message_attachment(
    db: Session,
    message_id: UUID,
    file_data: Dict[str, Any]
) -> MessageAttachment:
    """Ajouter pièce jointe à un message"""
    
    attachment = MessageAttachment(
        message_id=message_id,
        **file_data
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

# ========== FONCTIONS UTILITAIRES ==========

def _update_or_create_conversation(db: Session, message: Message):
    """Mettre à jour ou créer conversation"""
    
    if not message.conversation_id:
        return
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_key == message.conversation_id
    ).first()
    
    if not conversation:
        # Créer nouvelle conversation
        participant_ids = []
        if message.receiver_id:
            participant_ids = [message.sender_id, message.receiver_id]
        
        conversation = Conversation(
            conversation_key=message.conversation_id,
            conversation_type=message.message_type.value,
            participant_ids=participant_ids,
            participant_count=len(participant_ids),
            message_count=1,
            last_message_id=message.message_id,
            last_activity_at=message.sent_at
        )
        db.add(conversation)
    else:
        # Mettre à jour conversation existante
        conversation.message_count += 1
        conversation.last_message_id = message.message_id
        conversation.last_activity_at = message.sent_at
        conversation.updated_at = datetime.utcnow()

def get_message_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
    """Statistiques complètes de messaging"""
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Messages envoyés/reçus
    total_sent = db.query(Message).filter(Message.sender_id == user_id).count()
    total_received = db.query(Message).filter(Message.receiver_id == user_id).count()
    
    # Messages non lus
    unread_count = db.query(Message).filter(
        Message.receiver_id == user_id,
        Message.is_read == False,
        Message.is_deleted_by_receiver == False
    ).count()
    
    # Conversations actives
    active_conversations = db.query(Conversation).filter(
        Conversation.participant_ids.any(user_id),
        Conversation.is_active == True
    ).count()
    
    # Messages cette semaine/mois
    messages_this_week = db.query(Message).filter(
        Message.sender_id == user_id,
        Message.sent_at >= week_ago
    ).count()
    
    messages_this_month = db.query(Message).filter(
        Message.sender_id == user_id,
        Message.sent_at >= month_ago
    ).count()
    
    # Pièces jointes
    attachment_count = db.query(MessageAttachment).join(Message).filter(
        Message.sender_id == user_id
    ).count()
    
    # Réactions données/reçues
    reactions_given = db.query(MessageReaction).filter(
        MessageReaction.user_id == user_id
    ).count()
    
    reactions_received = db.query(MessageReaction).join(Message).filter(
        Message.sender_id == user_id
    ).count()
    
    return {
        "total_sent": total_sent,
        "total_received": total_received,
        "unread_count": unread_count,
        "active_conversations": active_conversations,
        "messages_this_week": messages_this_week,
        "messages_this_month": messages_this_month,
        "response_rate": 85.0,  # À calculer plus tard
        "average_response_time_hours": 2.5,  # À calculer plus tard
        "most_active_conversation": None,  # À implémenter
        "attachment_count": attachment_count,
        "reactions_given": reactions_given,
        "reactions_received": reactions_received
    }