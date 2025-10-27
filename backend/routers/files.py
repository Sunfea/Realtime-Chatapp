from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import schemas, models, auth
from file_service import save_uploaded_file, validate_file, get_file_url, delete_file, UPLOAD_DIR
from chat_crud import create_file_record, get_file_by_id, get_chat_files, delete_file_record
from websocket_manager import manager
import json

router = APIRouter()

@router.post("/chats/{chat_id}/files", response_model=schemas.FilePublic)
async def upload_file(
    chat_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify user is participant in this chat
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat or (chat.user1_id != current_user.id and chat.user2_id != current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Validate file
    is_valid, error_message = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    try:
        # Save file to filesystem
        file_path, unique_filename = save_uploaded_file(file, chat_id)
        
        # Create file record in database
        file_data = {
            "filename": file.filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "mime_type": file.content_type,
            "chat_id": chat_id,
            "uploaded_by": current_user.id
        }
        
        db_file = create_file_record(db, file_data)
        
        # Generate download URL
        download_url = get_file_url(file_path)
        
        # Notify other chat participants via WebSocket
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "file_uploaded",
                "file": {
                    "id": db_file.id,
                    "filename": db_file.filename,
                    "file_size": db_file.file_size,
                    "mime_type": db_file.mime_type,
                    "uploaded_by": db_file.uploaded_by,
                    "uploaded_at": db_file.uploaded_at.isoformat(),
                    "download_url": download_url
                },
                "chat_id": chat_id,
                "uploaded_by": current_user.id
            }),
            chat_id,
            exclude_user_id=current_user.id
        )
        
        return {
            **db_file.__dict__,
            "download_url": download_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/files/{file_path:path}")
async def get_file(file_path: str):
    """Serve uploaded files"""
    full_path = os.path.join(UPLOAD_DIR, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(full_path)

@router.get("/chats/{chat_id}/files", response_model=List[schemas.FilePublic])
async def get_files(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify user is participant in this chat
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat or (chat.user1_id != current_user.id and chat.user2_id != current_user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    
    files = get_chat_files(db, chat_id)
    
    # Add download URLs
    for file in files:
        file.download_url = get_file_url(file.file_path)
    
    return files

@router.delete("/files/{file_id}")
async def delete_uploaded_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    file = get_file_by_id(db, file_id)
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    # Delete file record from database
    success = delete_file_record(db, file_id, current_user.id)
    
    if success:
        # Schedule file deletion from filesystem
        background_tasks.add_task(delete_file, file.file_path)
        
        # Notify other chat participants
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "file_deleted",
                "file_id": file_id,
                "chat_id": file.chat_id,
                "deleted_by": current_user.id
            }),
            file.chat_id,
            exclude_user_id=current_user.id
        )
        
        return {"message": "File deleted successfully"}
    
    raise HTTPException(status_code=500, detail="Failed to delete file")