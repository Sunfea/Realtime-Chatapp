# config.py - SECURE VERSION
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    database_url: str = "sqlite:///./chat_app.db"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # For production - get from environment
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        
settings = Settings()