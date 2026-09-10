"""
Configuration settings for CryoNav AI API.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # CORS Settings
    cors_origins: list = ["*"]  # Allow all origins for hackathon demo
    
    # Data Settings
    data_dir: str = os.getenv("DATA_DIR", "data/scenarios")
    
    # Demo Settings
    max_scenario: int = 3
    default_scenario: int = 0
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()