try:
    from pydantic_settings import BaseSettings
    from typing import List
    import os
    from pathlib import Path
    
    print("✅ Wszystkie importy w config udane")
except ImportError as e:
    print(f"❌ Błąd importu w config: {e}")
    import traceback
    traceback.print_exc()
    raise


class Settings(BaseSettings):
    """Konfiguracja aplikacji z zmiennych środowiskowych"""
    
    # YouTube API settings
    youtube_api_key: str = ""
    days_back: int = 3  # Przywracam oryginalne ustawienie - 3 dni wstecz
    
    # FastAPI
    secret_key: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Feature flags
    enable_trend: bool = False
    
    # Scheduler
    scheduler_hour: int = 1
    scheduler_minute: int = 0
    timezone: str = "Europe/Warsaw"
    
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
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie lokalny katalog
        railway_volume = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if railway_volume:
            try:
                # Sprawdź czy katalog jest zapisywalny
                test_path = Path(railway_volume) / "data"
                test_path.mkdir(parents=True, exist_ok=True)
                # Sprawdź czy można zapisać plik testowy
                test_file = test_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()  # Usuń plik testowy
                print(f"✅ Railway volume dostępny i zapisywalny: {railway_volume}")
                return test_path
            except Exception as e:
                print(f"⚠️ Railway volume niedostępny lub tylko do odczytu: {e}")
                # Fallback do lokalnego katalogu
                return Path(self.data_dir)
        else:
            return Path(self.data_dir)
    
    @property
    def reports_path(self) -> Path:
        """Ścieżka do katalogu z raportami"""
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie lokalny katalog
        railway_volume = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if railway_volume:
            try:
                # Sprawdź czy katalog jest zapisywalny
                test_path = Path(railway_volume) / "reports"
                test_path.mkdir(parents=True, exist_ok=True)
                # Sprawdź czy można zapisać plik testowy
                test_file = test_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()  # Usuń plik testowy
                print(f"✅ Railway reports volume dostępny i zapisywalny: {railway_volume}")
                return test_path
            except Exception as e:
                print(f"⚠️ Railway reports volume niedostępny lub tylko do odczytu: {e}")
                # Fallback do lokalnego katalogu
                return Path(self.reports_dir)
        else:
            return Path(self.reports_dir)
    
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