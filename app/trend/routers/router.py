try:
    import logging
    from fastapi import APIRouter, Request, Query
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.templating import Jinja2Templates
    from app.trend.services.csv_processor import get_trend_data
    from datetime import date
    import pandas as pd
    import os
    from pathlib import Path
    
    print("✅ Wszystkie importy w trend router udane")
except ImportError as e:
    print(f"❌ Błąd importu w trend router: {e}")
    import traceback
    traceback.print_exc()
    raise

log = logging.getLogger("trend")
templates = Jinja2Templates(directory="hook-boost-web/templates")
router = APIRouter(prefix="/trend", tags=["trend"])

def get_top_videos_from_csv(category_name: str, limit: int = 15):
    """
    Prosta funkcja do czytania pliku CSV i zwracania top wideo.
    """
    try:
        # Ścieżka do katalogu raportów - użyj ustawień aplikacji
        from ...config.settings import settings
        reports_dir = settings.reports_path
        
        if not reports_dir.exists():
            log.warning(f"Katalog raportów nie istnieje: {reports_dir}")
            return []
        
        # Znajdź najnowszy plik CSV dla danej kategorii
        pattern = f"report_{category_name.upper()}_*.csv"
        csv_files = list(reports_dir.glob(pattern))
        
        if not csv_files:
            log.warning(f"Nie znaleziono plików CSV dla kategorii {category_name}")
            return []
        
        # Weź najnowszy plik (sortuj po nazwie)
        latest_file = sorted(csv_files)[-1]
        log.info(f"Używam pliku: {latest_file}")
        
        # Wczytaj CSV
        df = pd.read_csv(latest_file)
        
        # Sprawdź jakie kolumny są dostępne
        log.info(f"Dostępne kolumny: {list(df.columns)}")
        
        # Znajdź kolumnę z liczbą wyświetleń (może być View_Count, views_today, etc.)
        view_column = None
        for col in ['views_today', 'View_Count', 'views', 'View_Count_Today']:
            if col in df.columns:
                view_column = col
                break
        
        if not view_column:
            log.warning(f"Nie znaleziono kolumny z wyświetleniami w {latest_file}")
            return []
        
        # Znajdź kolumnę z tytułem
        title_column = None
        for col in ['title', 'Title', 'video_title']:
            if col in df.columns:
                title_column = col
                break
        
        if not title_column:
            log.warning(f"Nie znaleziono kolumny z tytułem w {latest_file}")
            return []
        
        # Znajdź kolumnę z nazwą kanału
        channel_column = None
        for col in ['channel', 'Channel_Name', 'channel_name']:
            if col in df.columns:
                channel_column = col
                break
        
        # Sortuj po wyświetleniach i weź top
        df_sorted = df.sort_values(by=view_column, ascending=False).head(limit)
        
        # Przygotuj dane do wyświetlenia
        top_videos = []
        for _, row in df_sorted.iterrows():
            video_data = {
                'title': str(row.get(title_column, 'Brak tytułu')),
                'views': int(row.get(view_column, 0)),
                'channel': str(row.get(channel_column, 'Nieznany kanał')) if channel_column else 'Nieznany kanał'
            }
            top_videos.append(video_data)
        
        log.info(f"Pomyślnie wczytano {len(top_videos)} wideo z {latest_file}")
        return top_videos
        
    except Exception as e:
        log.error(f"Błąd podczas wczytywania CSV: {e}")
        return []

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
    Strona HTML wyświetlająca top 15 najpopularniejszych wideo z pliku CSV.
    """
    try:
        log.info(f"Wyświetlanie top wideo dla kategorii {category_name}")
        
        # Pobierz top 15 wideo bezpośrednio z pliku CSV
        top_videos = get_top_videos_from_csv(category_name, limit=15)
        
        # Renderuj szablon
        return templates.TemplateResponse(
            "trend/local_trends.html",
            {
                "request": request,
                "category": category_name,
                "top_videos": top_videos,
                "current_date": date.today().strftime("%Y-%m-%d"),
                "total_videos": len(top_videos)
            }
        )
        
    except Exception as e:
        log.error(f"Błąd podczas wyświetlania top wideo dla {category_name}: {e}")
        
        return templates.TemplateResponse(
            "trend/local_trends.html",
            {
                "request": request,
                "category": category_name,
                "top_videos": [],
                "error": str(e),
                "current_date": date.today().strftime("%Y-%m-%d"),
                "total_videos": 0
            }
        )

@router.get("/rankings/{category_name}", response_class=HTMLResponse)
async def get_category_rankings(request: Request, category_name: str):
    """
    Wyświetla ranking top 10 filmów dla danej kategorii.
    Pokazuje podział na SHORTS i LONG FORM z historią pozycji.
    """
    try:
        # Import ranking managera
        from app.trend.services.ranking_manager import ranking_manager
        
        # Pobierz ranking dla kategorii
        ranking = ranking_manager.load_ranking(category_name)
        
        # Pobierz podsumowanie z trendami
        summary = ranking_manager.get_ranking_summary(category_name)
        
        # Renderuj szablon rankingów
        return templates.TemplateResponse(
            "trend/rankings.html",
            {
                "request": request,
                "category_name": category_name,
                "ranking": ranking,
                "summary": summary
            }
        )
        
    except Exception as e:
        log.error(f"Błąd podczas pobierania rankingu dla kategorii {category_name}: {e}")
        
        # W przypadku błędu zwróć szablon z pustymi danymi
        return templates.TemplateResponse(
            "trend/rankings.html",
            {
                "request": request,
                "category_name": category_name,
                "ranking": {
                    "category": category_name,
                    "last_updated": None,
                    "shorts": [],
                    "longform": [],
                    "history": {}
                },
                "summary": {"error": str(e)},
                "error": str(e)
            }
        )

@router.post("/rankings/{category_name}/clear")
async def clear_category_ranking(request: Request, category_name: str):
    """
    Czyści ranking dla danej kategorii, wymuszając regenerację z nową logiką.
    """
    try:
        from app.trend.services.ranking_manager import ranking_manager
        
        # Wyczyść ranking
        success = ranking_manager.clear_ranking(category_name)
        
        if success:
            return {
                "message": f"Ranking dla kategorii {category_name} został wyczyszczony",
                "category": category_name,
                "status": "cleared"
            }
        else:
            return {
                "message": f"Błąd podczas czyszczenia rankingu dla {category_name}",
                "category": category_name,
                "status": "error"
            }
            
    except Exception as e:
        log.error(f"Błąd podczas czyszczenia rankingu dla {category_name}: {e}")
        return {
            "message": f"Błąd podczas czyszczenia rankingu: {str(e)}",
            "category": category_name,
            "status": "error"
        }

@router.post("/rankings/{category_name}/regenerate")
async def regenerate_category_ranking(request: Request, category_name: str):
    """
    Regeneruje ranking dla danej kategorii używając najnowszych danych CSV i nowej logiki.
    """
    try:
        from app.trend.services.ranking_manager import ranking_manager
        from app.trend.services.csv_processor import get_trend_data
        from datetime import date
        
        # Wyczyść stary ranking
        ranking_manager.clear_ranking(category_name)
        
        # Pobierz najnowsze dane CSV
        videos = get_trend_data(category=category_name, report_date=date.today())
        
        if not videos:
            return {
                "message": f"Brak danych CSV dla kategorii {category_name}",
                "category": category_name,
                "status": "no_data"
            }
        
        # Wygeneruj nowy ranking z nową logiką
        ranking = ranking_manager.update_ranking(category_name, videos)
        
        return {
            "message": f"Ranking dla kategorii {category_name} został zregenerowany z nową logiką",
            "category": category_name,
            "status": "regenerated",
            "videos_count": len(videos),
            "shorts_count": len(ranking.get("shorts", [])),
            "longform_count": len(ranking.get("longform", [])),
            "last_updated": ranking.get("last_updated")
        }
            
    except Exception as e:
        log.error(f"Błąd podczas regeneracji rankingu dla {category_name}: {e}")
        return {
            "message": f"Błąd podczas regeneracji rankingu: {str(e)}",
            "category": category_name,
            "status": "error"
        }

@router.get("/modern/{category_name}")
async def get_modern_category_trends(request: Request, category_name: str):
    """
    NOWY endpoint do wyświetlania trendów dla danej kategorii.
    Używa nowego systemu RankingAnalyzer i plików JSON.
    """
    try:
        from datetime import date
        import json
        from pathlib import Path
        from app.config.settings import settings
        
        print(f"🔄 Nowy endpoint /modern/{category_name} - wczytuję ranking...")
        
        # Użyj naszych ustawień zamiast sztywnej ścieżki
        base_path = settings.reports_path
        today_str = date.today().strftime("%Y-%m-%d")
        ranking_path = base_path / f"ranking_{category_name.upper()}_{today_str}.json"
        
        print(f"📁 Szukam rankingu w: {ranking_path}")
        
        ranking_data = {"shorts": [], "longform": [], "error": "Brak rankingu"}
        if ranking_path.exists():
            print(f"✅ Znaleziono ranking: {ranking_path}")
            with open(ranking_path, 'r', encoding='utf-8') as f:
                ranking_data = json.load(f)
            print(f"📊 Wczytano ranking: {len(ranking_data.get('shorts', []))} shorts, {len(ranking_data.get('longform', []))} longform")
        else:
            print(f"⚠️ Brak rankingu dla {category_name} z dzisiaj: {ranking_path}")
            # Spróbuj znaleźć najnowszy dostępny ranking
            pattern = f"ranking_{category_name.upper()}_*.json"
            ranking_files = list(base_path.glob(pattern))
            if ranking_files:
                latest_ranking = sorted(ranking_files)[-1]
                print(f"📁 Używam najnowszego dostępnego rankingu: {latest_ranking}")
                with open(latest_ranking, 'r', encoding='utf-8') as f:
                    ranking_data = json.load(f)
                today_str = latest_ranking.stem.split('_')[-1]  # Wyciągnij datę z nazwy pliku
            else:
                print(f"❌ Brak jakichkolwiek rankingów dla {category_name}")
                ranking_data = {"shorts": [], "longform": [], "error": "Brak rankingów"}
        
        print(f"✅ Zwracam dane dla {category_name}: {len(ranking_data.get('shorts', []))} shorts, {len(ranking_data.get('longform', []))} longform")
        
        return templates.TemplateResponse(
            "trend/rankings.html",  # Użyj starego szablonu z pięknymi tabelami
            {
                "request": request,
                "category_name": category_name.capitalize(),
                "ranking": ranking_data,  # Dane w formacie starego systemu
                "summary": {
                    "category": category_name,
                    "last_updated": ranking_data.get('last_updated'),
                    "shorts_count": len(ranking_data.get('shorts', [])),
                    "longform_count": len(ranking_data.get('longform', [])),
                    "total_videos": ranking_data.get('total_videos_analyzed', 0)
                }
            }
        )
        
    except Exception as e:
        print(f"❌ Błąd w nowym endpoincie dla {category_name}: {e}")
        log.error(f"Błąd podczas pobierania nowoczesnego rankingu dla kategorii {category_name}: {e}")
        import traceback
        traceback.print_exc()
        
        # W przypadku błędu zwróć szablon z pustymi danymi
        return templates.TemplateResponse(
            "trend/modern_ranking.html",
            {
                "request": request,
                "category_name": category_name.capitalize(),
                "report_date": "Błąd",
                "ranking": {"shorts": [], "longform": [], "error": str(e)}
            }
        )
