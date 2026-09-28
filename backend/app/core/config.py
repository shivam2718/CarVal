"""
Application Configuration
Loads from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "CarVal Backend"
    API_VERSION: str = "0.1.0"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "development"
    
    # Service URLs (for calling Member 1 & 2 services)
    VISION_SERVICE_URL: str = "http://localhost:8001"
    DOCUMENT_AI_SERVICE_URL: str = "http://localhost:8002"
    
    # File Upload
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_DOCUMENT_SIZE_MB: int = 20
    UPLOAD_TEMP_DIR: str = "./temp_uploads"
    
    # Vision Configuration
    VISION_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Document AI Configuration
    DOCUMENT_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Database (Review 3+)
    DATABASE_URL: Optional[str] = "sqlite:///./carval.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
