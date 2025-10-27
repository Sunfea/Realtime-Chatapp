from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        # chat_id -> List[user_id]
        self.chat_connections: Dict[int, List[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            self.active_connections.pop(user_id)
        # Remove user from all chat rooms
        for chat_id, users in self.chat_connections.items():
            if user_id in users:
                users.remove(user_id)
        print(f"User {user_id} disconnected.")
    
    async def join_chat(self, user_id: int, chat_id: int):
        if chat_id not in self.chat_connections:
            self.chat_connections[chat_id] = []
        
        if user_id not in self.chat_connections[chat_id]:
            self.chat_connections[chat_id].append(user_id)
        
        print(f"User {user_id} joined chat {chat_id}")
    
    async def leave_chat(self, user_id: int, chat_id: int):
        if chat_id in self.chat_connections and user_id in self.chat_connections[chat_id]:
            self.chat_connections[chat_id].remove(user_id)
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)
    
    async def broadcast_to_chat(self, message: str, chat_id: int, exclude_user_id: int = None):
        if chat_id in self.chat_connections:
            for user_id in self.chat_connections[chat_id]:
                if user_id != exclude_user_id and user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message)

# Global instance
manager = ConnectionManager()