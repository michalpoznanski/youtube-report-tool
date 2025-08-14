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
    
    # Feature flags
    enable_trend: bool = False
    
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
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie domyślny katalog /mnt/volume
        railway_volume = os.getenv("RAILWAY_VOLUME_PATH")
        if railway_volume:
            return Path(railway_volume) / "data"
        else:
            return Path("/mnt/volume/data")
    
    @property
    def reports_path(self) -> Path:
        """Ścieżka do katalogu z raportami"""
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie domyślny katalog
        railway_volume = os.getenv("RAILWAY_VOLUME_PATH")
        if railway_volume:
            return Path(railway_volume) / "reports"
        else:
            return Path("/mnt/volume/reports")
    
    @property
    def backup_path(self) -> Path:
        """Ścieżka do katalogu z backupami"""
        return Path(self.backup_dir)
    
    def create_directories(self):
        """Tworzy wymagane katalogi"""
        try:
            print(f"📁 Tworzenie katalogów...")
            
            # Katalog danych
            self.data_path.mkdir(exist_ok=True)
            print(f"✅ Katalog danych: {self.data_path.absolute()}")
            
            # Katalog raportów (trwały)
            self.reports_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Katalog raportów: {self.reports_path.absolute()}")
            
            # Katalog backupów
            self.backup_path.mkdir(exist_ok=True)
            print(f"✅ Katalog backupów: {self.backup_path.absolute()}")
            
            # Katalog logów
            Path("logs").mkdir(exist_ok=True)
            print(f"✅ Katalog logów: logs/")
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia katalogów: {e}")
            raise


# Instancja ustawień
settings = Settings() 