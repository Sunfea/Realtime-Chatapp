from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from sqlalchemy import UniqueConstraint

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    username = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_chats_as_user1 = relationship("Chat", foreign_keys="Chat.user1_id", back_populates="user1")
    received_chats_as_user2 = relationship("Chat", foreign_keys="Chat.user2_id", back_populates="user2")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # First participant
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Second participant
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="received_chats_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="received_chats_as_user2")
    messages = relationship("Message", back_populates="chat")
    files = relationship("File", back_populates="chat") 
    
    # Correct unique constraint syntax
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_user_pair'),
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)  # ADD THIS
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    
class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploaded_by])