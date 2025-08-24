import logging
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ..services.csv_processor import CSVProcessor
from datetime import date

log = logging.getLogger("trend")
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/trend", tags=["trend"])

@router.get("/trends/{category_name}", response_class=HTMLResponse)
async def get_category_trends(request: Request, category_name: str):
    """
    Dynamiczny endpoint do wyświetlania trendów dla danej kategorii.
    Automatycznie pobiera ostatnie dostępne raporty CSV.
    """
    try:
        log.info(f"Pobieranie trendów dla kategorii {category_name}")
        
        # SPRAWDZENIE KATALOGU RAPORTÓW - DIAGNOZA
        import os
        reports_dir = "/mnt/volume/reports"
        log.info(f"🔍 Sprawdzam katalog raportów: {reports_dir}")
        log.info(f"🔍 Katalog istnieje: {os.path.exists(reports_dir)}")
        
        if os.path.exists(reports_dir):
            csv_files = [f for f in os.listdir(reports_dir) if f.endswith('.csv')]
            log.info(f"🔍 Znalezione pliki CSV: {csv_files}")
            
            # Sprawdź pliki dla konkretnej kategorii
            category_files = [f for f in csv_files if f.startswith(f"report_{category_name.upper()}_")]
            log.info(f"🔍 Pliki dla kategorii {category_name}: {category_files}")
        
        # Użyj CSVProcessor do pobrania rzeczywistych danych
        csv_processor = CSVProcessor()
        
        # Spróbuj pobrać dane z dzisiejszej daty
        videos = csv_processor.get_trend_data(category=category_name, report_date=date.today())
        report_date = date.today().strftime("%Y-%m-%d")
        
        if not videos:
            log.info(f"Brak danych dla dzisiejszej daty, sprawdzam dostępne daty")
            # Sprawdź dostępne daty dla kategorii
            available_dates = csv_processor.get_available_dates(category_name)
            
            if available_dates:
                # Użyj najnowszej dostępnej daty
                latest_date = available_dates[0]
                log.info(f"Używam najnowszej dostępnej daty: {latest_date}")
                videos = csv_processor.get_trend_data(category=category_name, report_date=date.fromisoformat(latest_date))
                report_date = latest_date
            else:
                log.warning(f"Brak dostępnych dat dla kategorii {category_name}")
                videos = []
        
        log.info(f"Pobrano {len(videos)} wideo dla kategorii {category_name} z daty {report_date}")
        
        # Renderuj szablon simple_report.html z danymi
        return templates.TemplateResponse(
            "trend/simple_report.html",
            {
                "request": request, 
                "category_name": category_name, 
                "videos": videos,
                "category": category_name,
                "report_date": report_date
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

@router.get("/api/trends/{category_name}")
async def get_category_trends_api(category_name: str, date: str = None):
    """
    API endpoint do pobierania danych trendów w formacie JSON.
    """
    try:
        csv_processor = CSVProcessor()
        
        if date:
            # Pobierz dane dla konkretnej daty
            videos = csv_processor.get_trend_data(category=category_name, report_date=date.fromisoformat(date))
        else:
            # Pobierz najnowsze dane
            videos = csv_processor.get_trend_data(category=category_name, report_date=date.today())
            
            if not videos:
                # Sprawdź dostępne daty
                available_dates = csv_processor.get_available_dates(category_name)
                if available_dates:
                    latest_date = available_dates[0]
                    videos = csv_processor.get_trend_data(category=category_name, report_date=date.fromisoformat(latest_date))
        
        if not videos:
            return JSONResponse(
                status_code=404,
                content={"error": f"Brak danych dla kategorii {category_name}"}
            )
        
        return JSONResponse(content={
            "category": category_name,
            "videos": videos,
            "count": len(videos)
        })
        
    except Exception as e:
        log.error(f"Błąd API dla kategorii {category_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Błąd serwera: {str(e)}"}
        )

@router.get("/api/trends/{category_name}/dates")
async def get_available_dates_api(category_name: str):
    """
    API endpoint do pobierania dostępnych dat dla kategorii.
    """
    try:
        csv_processor = CSVProcessor()
        available_dates = csv_processor.get_available_dates(category_name)
        
        return JSONResponse(content={
            "category": category_name,
            "available_dates": available_dates,
            "latest_date": available_dates[0] if available_dates else None
        })
        
    except Exception as e:
        log.error(f"Błąd API dla dat kategorii {category_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Błąd serwera: {str(e)}"}
        )

@router.post("/api/trends/analyze-all")
async def analyze_all_csvs_api():
    """
    API endpoint do ręcznego uruchomienia analizy wszystkich istniejących plików CSV.
    """
    try:
        from ..core.store.trend_store import analyze_all_existing_csvs
        
        log.info("Ręczne uruchomienie analizy wszystkich plików CSV")
        
        # Uruchom analizę w tle (może potrwać)
        result = analyze_all_existing_csvs()
        
        return JSONResponse(content={
            "message": "Analiza wszystkich plików CSV zakończona",
            "result": result
        })
        
    except Exception as e:
        log.error(f"Błąd podczas analizy wszystkich CSV: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Błąd serwera: {str(e)}"}
        )

@router.post("/api/trends/{category_name}/reanalyze")
async def reanalyze_category_api(category_name: str, date: str = None):
    """
    API endpoint do wymuszenia ponownej analizy kategorii.
    """
    try:
        from ..core.store.trend_store import force_reanalyze_category
        
        log.info(f"Wymuszenie ponownej analizy dla kategorii {category_name} {date or 'dzisiaj'}")
        
        success = force_reanalyze_category(category_name, date)
        
        if success:
            return JSONResponse(content={
                "message": f"Pomyślnie przeanalizowano ponownie {category_name}",
                "category": category_name,
                "date": date or "dzisiaj"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Nie udało się przeanalizować {category_name}"}
            )
        
    except Exception as e:
        log.error(f"Błąd podczas ponownej analizy {category_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Błąd serwera: {str(e)}"}
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
