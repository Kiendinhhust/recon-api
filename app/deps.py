"""
Dependencies and configuration for the recon API
"""
import os
from typing import Generator

from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/recon_db"
    
    # Redis for Celery
    redis_url: str = "redis://localhost:6379/0"
    
    # API settings
    api_title: str = "Recon API"
    api_version: str = "1.0.0"
    api_description: str = "Subdomain reconnaissance and screenshot capture API"
    
    # CORS settings - Allow all localhost ports for development
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080"
    ]
    
    # File storage
    jobs_directory: str = "./jobs"
    
    # Tool paths (assuming tools are in PATH)
    subfinder_path: str = "subfinder"
    amass_path: str = "amass"
    assetfinder_path: str = "assetfinder"
    httpx_path: str = "httpx"
    httprobe_path: str = "httprobe"
    anew_path: str = "anew"
    gowitness_path: str = "gowitness"
    wafw00f_path: str = "wafw00f"
    sourceleakhacker_path: str = "SourceLeakHacker.py"
    python_executable: str = "python"

    # Tool timeouts (in seconds)
    subfinder_timeout: int = 600  # 10 minutes
    amass_timeout: int = 1200     # 20 minutes
    assetfinder_timeout: int = 300 # 5 minutes
    httpx_timeout: int = 900      # 15 minutes
    httprobe_timeout: int = 600   # 10 minutes
    gowitness_timeout: int = 1800 # 30 minutes
    wafw00f_timeout: int = 900    # 15 minutes
    sourceleakhacker_timeout: int = 1800  # 30 minutes

    # WAF and Leak detection options
    enable_sourceleakhacker: bool = False
    sourceleakhacker_mode: str = "tiny"  # tiny or full
    sourceleakhacker_threads: int = 8
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_cors(app):
    """Setup CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_jobs_directory():
    """Create jobs directory if it doesn't exist"""
    os.makedirs(settings.jobs_directory, exist_ok=True)
