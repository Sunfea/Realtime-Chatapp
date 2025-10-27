import os
import uuid
from fastapi import UploadFile, HTTPException
from typing import Tuple
import shutil

UPLOAD_DIR = "uploads"
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")
DOCUMENTS_DIR = os.path.join(UPLOAD_DIR, "documents")

# Create directories if they don't exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_file_category(mime_type: str) -> str:
    """Determine file category based on MIME type"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type in ALLOWED_DOCUMENT_TYPES or mime_type.startswith('text/'):
        return 'document'
    else:
        return 'other'

def validate_file(file: UploadFile) -> Tuple[bool, str]:
    """Validate file type and size"""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File size {file_size} exceeds maximum allowed size {MAX_FILE_SIZE}"
    
    # Check MIME type
    file_category = get_file_category(file.content_type)
    if file_category == 'other':
        return False, f"File type {file.content_type} is not allowed"
    
    return True, ""

def save_uploaded_file(file: UploadFile, chat_id: int) -> Tuple[str, str]:
    """Save uploaded file and return file path and unique filename"""
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Determine save directory based on file type
    file_category = get_file_category(file.content_type)
    if file_category == 'image':
        save_dir = IMAGES_DIR
    else:
        save_dir = DOCUMENTS_DIR
    
    # Create chat-specific subdirectory
    chat_dir = os.path.join(save_dir, str(chat_id))
    os.makedirs(chat_dir, exist_ok=True)
    
    # Full file path
    file_path = os.path.join(chat_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path, unique_filename

def get_file_url(file_path: str) -> str:
    """Generate URL for accessing the file"""
    # Remove 'uploads/' from path for URL
    relative_path = file_path.replace(UPLOAD_DIR + os.sep, "").replace(os.sep, "/")
    return f"/files/{relative_path}"

def delete_file(file_path: str):
    """Delete file from filesystem"""
    if os.path.exists(file_path):
        os.remove(file_path)