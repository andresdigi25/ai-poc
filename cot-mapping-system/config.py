import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./cot_mappings.db"
    
    # Email Configuration
    email_imap_server: str = "imap.gmail.com"
    email_imap_port: int = 993
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    
    # Ollama Configuration
    ollama_model: str = "llama3.1:8b"
    ollama_host: str = "http://localhost:11434"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # n8n Configuration
    n8n_host: str = "http://localhost:5678"
    n8n_webhook_url: str = "http://localhost:8000/webhook/n8n"
    
    # Email Monitoring
    email_check_interval: int = 300  # 5 minutes
    email_folder: str = "INBOX"
    email_search_subject: str = "CoT"
    
    # Backup Configuration
    backup_interval: int = 86400  # 24 hours
    backup_keep_days: int = 30
    
    # Directories
    upload_dir: str = "uploads"
    backup_dir: str = "backups"
    log_dir: str = "logs"
    static_dir: str = "static"
    template_dir: str = "templates"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.upload_dir,
        settings.backup_dir,
        settings.log_dir,
        settings.static_dir,
        settings.template_dir
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Call on import
ensure_directories()