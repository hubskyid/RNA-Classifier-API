"""
Configuration management using environment variables
"""
import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5000))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
    API_WORKERS = int(os.getenv("API_WORKERS", 4))
    API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
    API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")
    
    # Gradio Configuration
    GRADIO_HOST = os.getenv("GRADIO_HOST", "127.0.0.1")
    GRADIO_PORT = int(os.getenv("GRADIO_PORT", 7860))
    GRADIO_SHARE = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    GRADIO_DEBUG = os.getenv("GRADIO_DEBUG", "true").lower() == "true"
    GRADIO_MAX_THREADS = int(os.getenv("GRADIO_MAX_THREADS", 40))
    
    # Database Configuration
    VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST", "localhost")
    VECTOR_DB_PORT = int(os.getenv("VECTOR_DB_PORT", 5000))
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "data" / "chromadb"))
    VECTOR_DB_COLLECTION = os.getenv("VECTOR_DB_COLLECTION", "rna_sequences")
    
    # ML Model Configuration
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models"))
    MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", str(BASE_DIR / "cache"))
    MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cpu")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))
    MAX_SEQUENCE_LENGTH = int(os.getenv("MAX_SEQUENCE_LENGTH", 50000))
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:7860,http://127.0.0.1:7860").split(",")
    
    # Logging Configuration
    LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    LOG_ROTATION = os.getenv("LOG_ROTATION", "size")
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 30))
    
    # Performance Configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 7200))  # 2 hours default timeout
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
    
    # Development Settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    TESTING = os.getenv("TESTING", "false").lower() == "true"
    
    @classmethod
    def get_db_url(cls) -> str:
        """Get database URL"""
        return f"http://{cls.VECTOR_DB_HOST}:{cls.VECTOR_DB_PORT}"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            Path(cls.LOG_DIR),
            Path(cls.VECTOR_DB_PATH),
            Path(cls.MODEL_PATH),
            Path(cls.MODEL_CACHE_DIR),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT == "development"


# Create singleton instance
config = Config()