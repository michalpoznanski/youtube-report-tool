from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Konfiguracja aplikacji z zmiennych środowiskowych"""
    
    # YouTube API
    youtube_api_key: str
    
    # FastAPI
    secret_key: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Scheduler
    scheduler_hour: int = 23
    scheduler_minute: int = 0
    days_back: int = 3
    
    # Storage
    data_dir: str = "data"
    reports_dir: str = "reports"
    backup_dir: str = "backups"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def data_path(self) -> Path:
        """Ścieżka do katalogu z danymi"""
        return Path(self.data_dir)
    
    @property
    def reports_path(self) -> Path:
        """Ścieżka do katalogu z raportami"""
        return Path(self.reports_dir)
    
    @property
    def backup_path(self) -> Path:
        """Ścieżka do katalogu z backupami"""
        return Path(self.backup_dir)
    
    def create_directories(self):
        """Tworzy wymagane katalogi"""
        self.data_path.mkdir(exist_ok=True)
        self.reports_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)


# Instancja ustawień
settings = Settings() 