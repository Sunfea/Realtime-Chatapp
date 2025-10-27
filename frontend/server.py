from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="ChatApp Frontend Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR)), name="static")

# Serve all frontend routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return serve_frontend("index.html")

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    return serve_frontend("pages/login.html")

@app.get("/register", response_class=HTMLResponse)
async def serve_register():
    return serve_frontend("pages/register.html")

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    return serve_frontend("pages/chat.html")

# Serve CSS files
@app.get("/css/{filename}")
async def serve_css(filename: str):
    return serve_static_file("css", filename)

# Serve JS files  
@app.get("/js/{filename}")
async def serve_js(filename: str):
    return serve_static_file("js", filename)

# Serve HTML files from pages directory
@app.get("/pages/{filename}")
async def serve_pages(filename: str):
    return serve_static_file("pages", filename)

# Helper function to serve static files
def serve_static_file(folder: str, filename: str):
    file_path = os.path.join(FRONTEND_DIR, folder, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

# Helper function to serve HTML files
def serve_frontend(html_file: str):
    file_path = os.path.join(FRONTEND_DIR, html_file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return HTMLResponse(content=file.read())
    raise HTTPException(status_code=404, detail="Page not found")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "frontend_server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)