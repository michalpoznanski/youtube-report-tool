from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
from pathlib import Path
import os

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

# Statyczne pliki
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Jeśli katalog static nie istnieje, pomiń montowanie
    pass

# Templates
templates = Jinja2Templates(directory="templates")

# Scheduler
scheduler = TaskScheduler() if TaskScheduler else None


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
    app.include_router(router, prefix="/api/v1", tags=["api"])


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
        "scheduler_running": scheduler.scheduler.running if scheduler else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 