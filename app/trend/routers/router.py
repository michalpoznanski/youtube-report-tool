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
        
        # Renderuj szablon simple_report.html z nowymi danymi
        return templates.TemplateResponse(
            "trend/simple_report.html",  # Nowy, prosty szablon
            {
                "request": request, 
                "category_name": category_name, 
                "videos": videos,
                "category": category_name,
                "report_date": date.today().strftime("%Y-%m-%d")
            }
        )
        
    except Exception as e:
        log.error(f"Błąd podczas pobierania trendów dla kategorii {category_name}: {e}")
        
        # W przypadku błędu zwróć szablon z pustymi danymi
        return templates.TemplateResponse(
            "trend/simple_report.html",
            {
                "request": request, 
                "category_name": category_name, 
                "videos": [],
                "category": category_name,
                "report_date": date.today().strftime("%Y-%m-%d"),
                "error": str(e)
            }
        )

@router.get("/local-trends/{category_name}", response_class=HTMLResponse)
async def get_local_trends_page(request: Request, category_name: str):
    """
    Strona HTML wyświetlająca wyniki lokalnej analizy trendów.
    """
    try:
        log.info(f"Wyświetlanie lokalnej analizy trendów dla kategorii {category_name}")
        
        # Pobierz dane lokalnej analizy przez API
        import requests
        api_url = f"http://localhost:8000/api/v1/trends/local-analysis/{category_name}"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                analysis_data = response.json()["data"]
                log.info(f"Pobrano lokalną analizę: {len(analysis_data.get('reports', []))} raportów")
            else:
                log.warning(f"Nie udało się pobrać lokalnej analizy: {response.status_code}")
                analysis_data = None
        except:
            log.warning("Nie udało się połączyć z API, używam przykładowych danych")
            analysis_data = None
        
        # Renderuj szablon
        return templates.TemplateResponse(
            "trend/local_trends.html",
            {
                "request": request,
                "category": category_name,
                "analysis_data": analysis_data,
                "current_date": date.today().strftime("%Y-%m-%d")
            }
        )
        
    except Exception as e:
        log.error(f"Błąd podczas wyświetlania lokalnej analizy dla {category_name}: {e}")
        
        return templates.TemplateResponse(
            "trend/local_trends.html",
            {
                "request": request,
                "category": category_name,
                "analysis_data": None,
                "error": str(e),
                "current_date": date.today().strftime("%Y-%m-%d")
            }
        )
