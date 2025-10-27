from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
import auth
from chat_crud import get_chat_between_users, create_chat, create_message, get_user_chats, get_chat_messages,mark_messages_as_read, get_unread_message_count
from websocket_manager import manager
import json

router = APIRouter()

# ADD THIS FUNCTION IF IT'S MISSING
def enhance_chat_with_user_data(chat, current_user_id: int, db: Session):
    """Add other_user information to chat object"""
    # Determine who the other user is
    other_user_id = chat.user2_id if chat.user1_id == current_user_id else chat.user1_id
    other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
    
    # Get last message if exists
    last_message = db.query(models.Message).filter(
        models.Message.chat_id == chat.id
    ).order_by(models.Message.sent_at.desc()).first()
    
    # Create the response data
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
    
    return chat_data

@router.post("/", response_model=schemas.ChatPublic)
async def create_or_get_chat(
    recipient_username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check if recipient exists
    recipient = db.query(models.User).filter(models.User.username == recipient_username).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow self-chat
    if recipient.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")
    
    # Check if chat already exists
    existing_chat = get_chat_between_users(db, current_user.id, recipient.id)
    if existing_chat:
        # Return the existing chat with proper other_user data
        return enhance_chat_with_user_data(existing_chat, current_user.id, db)
    
    # Create new chat
    new_chat = create_chat(db, current_user.id, recipient.id)
    # Return the new chat with proper other_user data
    return enhance_chat_with_user_data(new_chat, current_user.id, db)

@router.get("/", response_model=List[schemas.ChatPublic])
async def get_my_chats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    chats = get_user_chats(db, current_user.id)
    return chats

@router.post("/{chat_id}/messages", response_model=schemas.MessagePublic)
async def send_message(
    chat_id: int,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify user is participant in this chat
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat or (chat.user1_id != current_user.id and chat.user2_id != current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Create message in database
    db_message = create_message(db, message, chat_id, current_user.id)
    
    # Broadcast via WebSocket to other participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "new_message",
            "message": {
                "id": db_message.id,
                "content": db_message.content,
                "sender_id": db_message.sender_id,
                "sent_at": db_message.sent_at.isoformat(),
                "is_read": db_message.is_read
            },
            "chat_id": chat_id
        }),
        chat_id,
        exclude_user_id=current_user.id
    )
    
    print(f"Message broadcasted to chat {chat_id}")
    return db_message

@router.get("/{chat_id}/messages", response_model=List[schemas.MessagePublic])
async def get_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    messages = get_chat_messages(db, chat_id, current_user.id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return messages

@router.put("/messages/read")
async def mark_messages_read(
    read_data: schemas.MessageReadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Mark multiple messages as read"""
    updated_messages = mark_messages_as_read(db, read_data.message_ids, current_user.id)
    
    # Notify senders via WebSocket that their messages were read
    for message in updated_messages:
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "message_read",
                "message_id": message.id,
                "reader_id": current_user.id,
                "chat_id": message.chat_id,
                "read_at": message.read_at.isoformat() if message.read_at else None
            }),
            message.chat_id,
            exclude_user_id=current_user.id
        )
    
    return {"updated_count": len(updated_messages)}

@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get total unread messages count for current user"""
    count = get_unread_message_count(db, current_user.id)
    return {"unread_count": count}

