from fastapi import FastAPI
from database import engine
import models
from routers import auth, users, chats
from fastapi.middleware.cors import CORSMiddleware
from routers import files


# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chats.router, prefix="/chats", tags=["chats"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(files.router, tags=['files'])

@app.get("/")
def read_root():
    return {"message": "Chat App API is running"}

from fastapi import WebSocket, WebSocketDisconnect
from websocket_manager import manager
import json

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for any message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different types of messages
            if message_data["type"] == "join_chat":
                await manager.join_chat(user_id, message_data["chat_id"])
                print(f"User {user_id} joined chat {message_data['chat_id']}")
            
            elif message_data["type"] == "typing":
                # Broadcast typing indicator to other users in chat
                await manager.broadcast_to_chat(
                    json.dumps({
                        "type": "typing",
                        "user_id": user_id,
                        "chat_id": message_data["chat_id"],
                        "is_typing": message_data["is_typing"]
                    }),
                    message_data["chat_id"],
                    exclude_user_id=user_id
                )
                print(f"User {user_id} typing in chat {message_data['chat_id']}")
            
            elif message_data["type"] == "message_read":
                # Handle read receipts
                await manager.broadcast_to_chat(
                    json.dumps({
                        "type": "message_read",
                        "message_id": message_data["message_id"],
                        "reader_id": user_id,
                        "chat_id": message_data["chat_id"]
                    }),
                    message_data["chat_id"],
                    exclude_user_id=user_id
                )
            
            elif message_data["type"] == "file_uploaded":
                # Handle file upload notifications
                await manager.broadcast_to_chat(
                    json.dumps({
                        "type": "file_uploaded",
                        "file": message_data["file"],
                        "chat_id": message_data["chat_id"],
                        "uploaded_by": user_id
                    }),
                    message_data["chat_id"],
                    exclude_user_id=user_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconnected from WebSocket")
        