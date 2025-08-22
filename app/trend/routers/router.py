import logging
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.trend.services.csv_processor import get_trend_data
from datetime import date

log = logging.getLogger("trend")
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/trend", tags=["trend"])

@router.get("/trends/{category_name}", response_class=HTMLResponse)
async def get_category_trends(request: Request, category_name: str):
    """
    Dynamiczny endpoint do wyświetlania trendów dla danej kategorii.
    Używa nowego serwisu csv_processor do pobierania danych.
    """
    try:
        # Pobierz dane trendów używając nowego serwisu
        videos = get_trend_data(category=category_name, report_date=date.today())
        
        log.info(f"Pobrano {len(videos)} wideo dla kategorii {category_name}")
        
        # Renderuj szablon dashboard.html z nowymi danymi
        return templates.TemplateResponse(
            "trend/podcast/dashboard.html",  # Na razie używamy istniejącego szablonu
            {
                "request": request, 
                "category_name": category_name, 
                "videos": videos
            }
        )
        
    except Exception as e:
        log.error(f"Błąd podczas pobierania trendów dla kategorii {category_name}: {e}")
        
        # W przypadku błędu zwróć szablon z pustymi danymi
        return templates.TemplateResponse(
            "trend/podcast/dashboard.html",
            {
                "request": request, 
                "category_name": category_name, 
                "videos": [],
                "error": str(e)
            }
        )
