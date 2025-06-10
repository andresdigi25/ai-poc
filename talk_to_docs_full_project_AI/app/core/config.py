from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Talk to Docs"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/talk_to_docs")
    
    # FTP Settings
    FTP_HOST: str = os.getenv("FTP_HOST", "")
    FTP_USER: str = os.getenv("FTP_USER", "")
    FTP_PASSWORD: str = os.getenv("FTP_PASSWORD", "")
    
    # Ollama Settings
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 