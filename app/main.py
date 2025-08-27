from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
from pathlib import Path
import os

print("🚀🚀🚀 URUCHAMIAM NAJNOWSZĄ WERSJĘ Z 23 SIERPNIA - NOWY INTERFEJS! 🚀🚀🚀")

# Załaduj zmienne środowiskowe z .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using system env vars")
except Exception as e:
    print(f"⚠️ Error loading .env: {e}")

# DEBUG: Sprawdź zmienne środowiskowe
print("🔍 DEBUG: Sprawdzam zmienne środowiskowe...")
print(f"🔍 ENABLE_TREND = {os.environ.get('ENABLE_TREND', 'NOT_SET')}")
print(f"🔍 PYTHONPATH = {os.environ.get('PYTHONPATH', 'NOT_SET')}")
print(f"🔍 PWD = {os.environ.get('PWD', 'NOT_SET')}")
print(f"🔍 Current working directory = {os.getcwd()}")

# Log startowy z branch, SHA i konfiguracją
try:
    import subprocess
    git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
    git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()[:8]
    print(f"🚀 STARTUP: Branch={git_branch}, SHA={git_sha}, ENABLE_TREND={os.environ.get('ENABLE_TREND', 'NOT_SET')}")
except Exception as e:
    print(f"⚠️ Nie można pobrać informacji Git: {e}")
    git_branch = "unknown"
    git_sha = "unknown"

# Import z obsługą błędów
try:
    from .config import settings
    from .api import router
    from .scheduler import TaskScheduler
except ImportError as e:
    print(f"Błąd importu: {e}")
    # Fallback settings
    class FallbackSettings:
        log_level = "INFO"
        log_file = "logs/app.log"
        allowed_origins = ["*"]
        def create_directories(self):
            Path("logs").mkdir(exist_ok=True)
    
    settings = FallbackSettings()
    router = None
    TaskScheduler = None

# Konfiguracja logowania
try:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
except Exception:
    # Fallback - tylko console logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

# Tworzenie aplikacji FastAPI
app = FastAPI(
    title="Hook Boost Web",
    description="Aplikacja webowa do raportowania danych z kanałów YouTube",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statyczne pliki i templates z fallback
import os
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Fallback dla różnych struktur katalogów
tpl_root = (
    "hook-boost-web/templates" if os.path.isdir("hook-boost-web/templates") else "templates"
)
static_root = (
    "hook-boost-web/static" if os.path.isdir("hook-boost-web/static") else "static"
)

print(f"🔍 DEBUG: Templates directory = {tpl_root}")
print(f"🔍 DEBUG: Static directory = {static_root}")

# Templates
templates = Jinja2Templates(directory=tpl_root)

# Statyczne pliki
try:
    app.mount("/static", StaticFiles(directory=static_root), name="static")
    print(f"✅ Static files mounted from {static_root}")
except RuntimeError as e:
    print(f"⚠️ Static files mount failed: {e}")
    # Jeśli katalog static nie istnieje, pomiń montowanie
    pass

# Scheduler
scheduler = TaskScheduler() if TaskScheduler else None

# Upewnij się, że dane są załadowane przed startem API
if scheduler and scheduler.state_manager:
    print("🔄 Wymuszanie załadowania danych przed startem API...")
    scheduler.state_manager.load_all_data()
    print("✅ Dane załadowane przed startem API")


@app.on_event("startup")
async def startup_event():
    """Event uruchamiany przy starcie aplikacji"""
    try:
        logger.info("Uruchamianie aplikacji Hook Boost Web...")
        
        # Utwórz wymagane katalogi
        settings.create_directories()
        
        # Uruchom scheduler jeśli dostępny
        if scheduler:
            scheduler.start()
        
        logger.info("Aplikacja uruchomiona pomyślnie!")
        
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania aplikacji: {e}")
        # Nie rzucaj błędu - pozwól aplikacji się uruchomić


@app.on_event("shutdown")
async def shutdown_event():
    """Event uruchamiany przy zatrzymaniu aplikacji"""
    try:
        logger.info("Zatrzymywanie aplikacji...")
        
        # Zatrzymaj scheduler jeśli dostępny
        if scheduler:
            scheduler.stop()
        
        logger.info("Aplikacja zatrzymana pomyślnie!")
        
    except Exception as e:
        logger.error(f"Błąd podczas zatrzymywania aplikacji: {e}")


# Dodaj router API jeśli dostępny
if router:
    # Przekaż instancję schedulera do API
    try:
        from .api.routes import set_task_scheduler
        if scheduler:
            set_task_scheduler(scheduler)
    except ImportError:
        pass
    
    app.include_router(router, prefix="/api/v1", tags=["api"])

# --- Trend module (feature-flag) ---
print("🔍 DEBUG: Sprawdzam moduł trendów...")
print(f"🔍 ENABLE_TREND value = '{os.environ.get('ENABLE_TREND','false')}'")
print(f"🔍 ENABLE_TREND type = {type(os.environ.get('ENABLE_TREND','false'))}")
print(f"🔍 ENABLE_TREND.lower() = '{os.environ.get('ENABLE_TREND','false').lower()}'")
print(f"🔍 Comparison result = {os.environ.get('ENABLE_TREND','false').lower()=='true'}")

# Dodatkowe sprawdzenie - może zmienna jest ustawiona w inny sposób
enable_trend = (
    os.environ.get('ENABLE_TREND', 'false').lower() == 'true' or
    os.environ.get('ENABLE_TREND', 'false') == 'true' or
    os.environ.get('ENABLE_TREND', 'false') == True
)

print(f"🔍 DEBUG: Final enable_trend decision = {enable_trend}")

if enable_trend:
    print("🔍 DEBUG: ENABLE_TREND is true, loading trend module...")
    try:
        from app.trend.routers.router import router as trend_router
        print("🔍 DEBUG: Trend router imported successfully")
        app.include_router(trend_router)
        print("✅ Trend module loaded successfully")
        try:
            from app.trend.core.scheduler_bind import register_trend_job
            register_trend_job(scheduler, category='PODCAST')
            print("✅ Trend scheduler attached")
        except Exception as e:
            print(f"⚠️ Trend scheduler attach failed: {e}")
    except Exception as e:
        print(f"❌ Trend module failed to load: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ℹ️ Trend module disabled (ENABLE_TREND!=true)")
    # Fallback - spróbuj załadować moduł trendów mimo wszystko
    print("🔄 DEBUG: Próbuję załadować moduł trendów mimo wszystko...")
    try:
        from app.trend.routers.router import router as trend_router
        print("🔍 DEBUG: Trend router imported successfully (fallback)")
        app.include_router(trend_router)
        print("✅ Trend module loaded successfully (fallback)")
    except Exception as e:
        print(f"❌ Trend module fallback failed: {e}")
        import traceback
        traceback.print_exc()




@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Strona główna aplikacji"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "branch": git_branch,
        "sha": git_sha,
        "enable_trend": os.environ.get("ENABLE_TREND", "NOT_SET"),
        "templates_dir": tpl_root,
        "static_dir": static_root,
        "scheduler_running": scheduler.scheduler.running if scheduler else False
    }


@app.get("/test-trend-routing")
async def test_trend_routing():
    """Test endpoint żeby sprawdzić czy routing trendów działa"""
    return {
        "message": "✅ Trend routing test",
        "enable_trend": os.environ.get("ENABLE_TREND", "NOT_SET"),
        "trend_endpoints": [
            "/trend/local-trends/PODCAST",
            "/trend/local-trends/MOTO", 
            "/trend/local-trends/POLITYKA"
        ],
        "timestamp": "2025-08-25"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 