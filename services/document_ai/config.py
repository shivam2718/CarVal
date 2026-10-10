"""
Document AI Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Document AI service settings"""
    
    # Service
    SERVICE_NAME: str = "Document AI"
    SERVICE_VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # OCR Configuration
    OCR_BACKEND: str = "pytesseract"  # pytesseract, google, aws-textract
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    
    # Extraction Configuration
    RC_CONFIDENCE_THRESHOLD: float = 0.75
    INSURANCE_CONFIDENCE_THRESHOLD: float = 0.70
    SERVICE_CONFIDENCE_THRESHOLD: float = 0.75
    
    # File handling
    TEMP_DIR: str = "/tmp/carval_documents"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_FORMATS: list = ["pdf", "jpg", "jpeg", "png", "bmp"]
    
    # Tesseract path (if not in system PATH)
    TESSERACT_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
