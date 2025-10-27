from pydantic import BaseModel, EmailStr, validator, field_validator
from datetime import datetime
from typing import List, Optional
import re

# ===== USER SCHEMAS =====
class UserCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def username_alphanumeric_lowercase(cls, v):
        v = v.lower().strip()
        
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long.')
        if len(v) > 20:
            raise ValueError('Username must not exceed 20 characters.')
        if not re.match("^[a-z0-9]+$", v):
            raise ValueError('Username must be alphanumeric (letters and numbers only). No spaces, uppercase, or special characters.')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Full name cannot be empty.')
        if len(v) > 100:
            raise ValueError('Full name is too long.')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserPublic(BaseModel):
    id: int
    full_name: str
    username: str
    
    class Config:
        from_attributes = True

class UserPrivate(UserPublic):
    email: EmailStr

# ===== CHAT & MESSAGE SCHEMAS =====
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessagePublic(MessageBase):
    id: int
    sender_id: int
    sent_at: datetime
    is_read: bool
    read_at: Optional[datetime] = None  # ADD THIS
    
    class Config:
        from_attributes = True

class MessageReadUpdate(BaseModel):
    message_ids: List[int]

class ChatParticipantInfo(BaseModel):
    id: int
    username: str
    full_name: str
    
    class Config:
        from_attributes = True

class ChatPublic(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    last_message_at: datetime
    other_user: ChatParticipantInfo  # The user you're chatting with
    last_message: Optional[MessagePublic] = None
    
    @field_validator('last_message_at', mode='before')
    @classmethod
    def ensure_last_message_at(cls, v):
        # If last_message_at is None, use current time
        if v is None:
            return datetime.now()
        return v
    
    class Config:
        from_attributes = True

class ChatWithMessages(ChatPublic):
    messages: List[MessagePublic] = []

# ===== SEARCH SCHEMAS =====
class UserSearchResult(BaseModel):
    id: int
    username: str
    full_name: str
    
    class Config:
        from_attributes = True

# ===== TOKEN SCHEMAS =====
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# FILE SCHEMA:=============================================================
    
class FileBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str

class FileCreate(FileBase):
    pass

class FilePublic(FileBase):
    id: int
    chat_id: int
    uploaded_by: int
    uploaded_at: datetime
    download_url: str
    
    class Config:
        from_attributes = True

class MessageWithFile(BaseModel):
    content: Optional[str] = None
    file_id: Optional[int] = None