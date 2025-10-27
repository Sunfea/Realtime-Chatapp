from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import models
import schemas
from typing import List, Optional

def get_chat_between_users(db: Session, user1_id: int, user2_id: int):
    """Find chat between two users (order doesn't matter)"""
    return db.query(models.Chat).filter(
        or_(
            and_(models.Chat.user1_id == user1_id, models.Chat.user2_id == user2_id),
            and_(models.Chat.user1_id == user2_id, models.Chat.user2_id == user1_id)
        )
    ).first()

def create_chat(db: Session, user1_id: int, user2_id: int):
    """Create a new chat between two users"""
    # Ensure consistent ordering to avoid duplicate chats
    smaller_id, larger_id = sorted([user1_id, user2_id])
    
    db_chat = models.Chat(user1_id=smaller_id, user2_id=larger_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    # Add other_user data directly to the chat object
    other_user_id = user2_id if user1_id == smaller_id else user1_id
    other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
    
    db_chat.other_user = {
        "id": other_user.id,
        "username": other_user.username,
        "full_name": other_user.full_name
    }
    
    return db_chat

def create_message(db: Session, message: schemas.MessageCreate, chat_id: int, sender_id: int):
    """Create a new message in a chat"""
    db_message = models.Message(
        content=message.content,
        chat_id=chat_id,
        sender_id=sender_id
    )
    db.add(db_message)
    
    # Update chat's last message timestamp
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    chat.last_message_at = db_message.sent_at
    
    db.commit()
    db.refresh(db_message)
    return db_message

def get_user_chats(db: Session, user_id: int):
    """Get all chats for a user with the other user's info"""
    chats = db.query(models.Chat).filter(
        or_(models.Chat.user1_id == user_id, models.Chat.user2_id == user_id)
    ).order_by(models.Chat.last_message_at.desc()).all()
    
    # Enhance with other user's info and last message
    enhanced_chats = []
    for chat in chats:
        # Determine who the other user is
        other_user_id = chat.user2_id if chat.user1_id == user_id else chat.user1_id
        other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
        
        # Get last message if exists
        last_message = db.query(models.Message).filter(
            models.Message.chat_id == chat.id
        ).order_by(models.Message.sent_at.desc()).first()
        
        # Create enhanced chat data
        chat_data = {
            "id": chat.id,
            "user1_id": chat.user1_id,
            "user2_id": chat.user2_id,
            "created_at": chat.created_at,
            "last_message_at": chat.last_message_at,
            "other_user": {
                "id": other_user.id,
                "username": other_user.username,
                "full_name": other_user.full_name
            },
            "last_message": last_message
        }
        enhanced_chats.append(chat_data)
    
    return enhanced_chats

def get_chat_messages(db: Session, chat_id: int, user_id: int):
    """Get all messages for a chat if user is participant"""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    
    if not chat or (chat.user1_id != user_id and chat.user2_id != user_id):
        return None
    
    return db.query(models.Message).filter(
        models.Message.chat_id == chat_id
    ).order_by(models.Message.sent_at).all()

def mark_messages_as_read(db: Session, message_ids: List[int], reader_id: int):
    """Mark messages as read by a user"""
    messages = db.query(models.Message).filter(
        models.Message.id.in_(message_ids),
        models.Message.sender_id != reader_id  # Can't mark own messages as read
    ).all()
    
    for message in messages:
        message.is_read = True
        message.read_at = func.now()
    
    db.commit()
    return messages

def get_unread_message_count(db: Session, user_id: int):
    """Get count of unread messages for a user"""
    return db.query(models.Message).join(models.Chat).filter(
        models.Message.sender_id == user_id,
        models.Message.is_read == False,
        or_(
            models.Chat.user1_id != user_id,
            models.Chat.user2_id != user_id
        )
    ).count()
    
    
def create_file_record(db: Session, file_data: dict):
    """Create file record in database"""
    db_file = models.File(**file_data)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file_by_id(db: Session, file_id: int):
    """Get file by ID"""
    return db.query(models.File).filter(models.File.id == file_id).first()

def get_chat_files(db: Session, chat_id: int):
    """Get all files in a chat"""
    return db.query(models.File).filter(models.File.chat_id == chat_id).order_by(models.File.uploaded_at.desc()).all()

def delete_file_record(db: Session, file_id: int, user_id: int):
    """Delete file record from database"""
    file = db.query(models.File).filter(
        models.File.id == file_id,
        models.File.uploaded_by == user_id
    ).first()
    
    if file:
        db.delete(file)
        db.commit()
        return True
    return False