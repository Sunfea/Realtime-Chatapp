💬 ChatApp - Real-time Messenger

A modern chat application with real-time messaging, file sharing, and secure authentication.

🚀 Features
💬 Real-time Chat
Instant messaging with WebSockets

Typing indicators & read receipts

One-on-one private chats

Persistent chat history

🔐 Security
JWT authentication

Password encryption

CORS protection

Secure file uploads

📱 User Experience
Responsive design (mobile & desktop)

Modern, clean UI

User search & profiles

Drag & drop file sharing

📁 File Sharing
Multiple file type support

10MB size limit

Secure storage

Easy downloads

🛠 Tech Stack
Backend
FastAPI - Modern Python web framework

SQLAlchemy - Database ORM

SQLite/PostgreSQL - Database

JWT - Authentication

WebSockets - Real-time communication

Pydantic - Data validation

Frontend
Vanilla JavaScript - No framework dependencies

CSS3 - Modern styling with variables

HTML5 - Semantic markup

Fetch API - HTTP requests

WebSocket API - Real-time updates

🏗 Architecture
text
chatapp/
├── backend/          # FastAPI + Python
│   ├── routers/     # API routes
│   ├── models.py    # Database models
│   └── main.py      # App entry point
└── frontend/        # Vanilla JS
    ├── index.html   # Single page app
    ├── css/         # Styling
    └── js/          # Application logic
