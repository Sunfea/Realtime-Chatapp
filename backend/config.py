from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./chat_app.db"
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    
    class Config:
        env_file = ".env"
        
settings = Settings()