from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
from pathlib import Path

from .config import settings
from .api import router
from .scheduler import TaskScheduler

# Konfiguracja logowania
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
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
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Scheduler
scheduler = TaskScheduler()


@app.on_event("startup")
async def startup_event():
    """Event uruchamiany przy starcie aplikacji"""
    try:
        logger.info("Uruchamianie aplikacji Hook Boost Web...")
        
        # Uruchom scheduler
        scheduler.start()
        
        logger.info("Aplikacja uruchomiona pomyślnie!")
        
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania aplikacji: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Event uruchamiany przy zatrzymaniu aplikacji"""
    try:
        logger.info("Zatrzymywanie aplikacji...")
        
        # Zatrzymaj scheduler
        scheduler.stop()
        
        logger.info("Aplikacja zatrzymana pomyślnie!")
        
    except Exception as e:
        logger.error(f"Błąd podczas zatrzymywania aplikacji: {e}")


# Dodaj router API
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
        "scheduler_running": scheduler.scheduler.running
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 