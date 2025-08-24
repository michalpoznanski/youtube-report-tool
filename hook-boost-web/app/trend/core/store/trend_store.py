import os, json, datetime as dt
from typing import Dict, Any
import pandas as pd
from ..dispatcher import analyze_category
from ...services.csv_processor import CSVProcessor

def base_dir():
    root = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume")
    path = os.path.join(root, "guest_analysis", "trends")
    os.makedirs(path, exist_ok=True)
    return path

def cat_dir(category: str):
    d = os.path.join(base_dir(), category.lower())
    os.makedirs(d, exist_ok=True)
    return d

def trends_path(category: str):
    return os.path.join(cat_dir(category), "video_trends.json")

def growth_path(category: str, report_date: str):
    return os.path.join(cat_dir(category), f"video_growth_{report_date}.json")

def stats_path(category: str, report_date: str):
    return os.path.join(cat_dir(category), f"stats_{report_date}.json")

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, ensure_ascii=False, indent=2, fp=f)

def auto_analyze_and_save(category: str, report_date: str = None):
    """
    Automatycznie analizuje plik CSV i zapisuje wyniki do trend_store.
    Wywoływane po wygenerowaniu pliku CSV przez scheduler.
    
    Args:
        category (str): Nazwa kategorii (np. "PODCAST")
        report_date (str): Data raportu w formacie YYYY-MM-DD (domyślnie dzisiejsza)
    """
    try:
        if report_date is None:
            report_date = dt.date.today().strftime("%Y-%m-%d")
        
        print(f"🔄 Auto-analiza: Rozpoczynam analizę dla {category} z datą {report_date}")
        
        # Użyj CSVProcessor do wczytania danych
        csv_processor = CSVProcessor()
        videos_data = csv_processor.get_trend_data(category, dt.date.fromisoformat(report_date))
        
        if not videos_data:
            print(f"⚠️ Auto-analiza: Brak danych do analizy dla {category} {report_date}")
            return False
        
        print(f"✅ Auto-analiza: Wczytano {len(videos_data)} wideo dla {category}")
        
        # Konwertuj dane z CSVProcessor na DataFrame dla dispatcher
        df = pd.DataFrame(videos_data)
        
        # Mapuj kolumny z CSVProcessor na wymagane przez dispatcher
        column_mapping = {
            'title': 'Title',
            'views': 'View_Count', 
            'delta': 'delta',
            'video_type': 'video_type',
            'video_id': 'Video_ID',
            'channel': 'Channel_Name',
            'duration': 'Duration',
            'description': 'Description',
            'tags': 'Tags',
            'like_count': 'Like_Count',
            'topic_categories': 'Topic_Categories',
            'channel_id': 'Channel_ID',
            'date_published': 'Date_of_Publishing',
            'hour_published': 'Hour_GMT2'
        }
        
        # Zmień nazwy kolumn
        df = df.rename(columns=column_mapping)
        
        # Analizuj dane używając dispatcher
        analysis_result = analyze_category(category, df)
        
        # Zapisz wyniki analizy
        save_analysis_results(category, report_date, analysis_result, videos_data)
        
        print(f"✅ Auto-analiza: Zakończono analizę i zapisano wyniki dla {category} {report_date}")
        return True
        
    except Exception as e:
        print(f"❌ Auto-analiza: Błąd podczas analizy {category} {report_date}: {e}")
        return False

def save_analysis_results(category: str, report_date: str, analysis_result: Dict[str, Any], raw_data: list):
    """
    Zapisuje wyniki analizy do odpowiednich plików JSON.
    
    Args:
        category (str): Nazwa kategorii
        report_date (str): Data raportu
        analysis_result (Dict): Wyniki analizy z dispatcher
        raw_data (list): Surowe dane z CSV
    """
    try:
        # Zapisz główne trendy
        trends_data = {
            "category": category,
            "report_date": report_date,
            "analysis_timestamp": dt.datetime.now().isoformat(),
            "total_videos": len(raw_data),
            "top_rankings": analysis_result.get("rank_top", []),
            "stats": analysis_result.get("stats", {}),
            "analysis_type": analysis_result.get("type", "unknown")
        }
        
        save_json(trends_path(category), trends_data)
        
        # Zapisz dane wzrostu (delta)
        growth_data = {
            "category": category,
            "report_date": report_date,
            "analysis_timestamp": dt.datetime.now().isoformat(),
            "videos": raw_data
        }
        
        save_json(growth_path(category, report_date), growth_data)
        
        # Zapisz statystyki
        stats_data = {
            "category": category,
            "report_date": report_date,
            "analysis_timestamp": dt.datetime.now().isoformat(),
            "stats": analysis_result.get("stats", {}),
            "summary": {
                "total_videos": len(raw_data),
                "total_views": sum(v.get('views', 0) for v in raw_data),
                "total_delta": sum(v.get('delta', 0) for v in raw_data),
                "shorts_count": len([v for v in raw_data if v.get('video_type') == 'Shorts']),
                "longform_count": len([v for v in raw_data if v.get('video_type') == 'Longform'])
            }
        }
        
        save_json(stats_path(category, report_date), stats_data)
        
        print(f"💾 Zapisano wyniki analizy dla {category} {report_date}")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania wyników analizy: {e}")

def get_latest_analysis(category: str) -> Dict[str, Any]:
    """
    Pobiera najnowszą analizę dla danej kategorii.
    
    Args:
        category (str): Nazwa kategorii
        
    Returns:
        Dict: Najnowsze dane analizy lub pusty słownik
    """
    try:
        # Sprawdź czy istnieje plik z trendami
        trends_file = trends_path(category)
        if not os.path.exists(trends_file):
            return {}
        
        # Wczytaj dane
        trends_data = load_json(trends_file)
        
        # Sprawdź czy dane nie są zbyt stare (więcej niż 7 dni)
        if "analysis_timestamp" in trends_data:
            try:
                analysis_time = dt.datetime.fromisoformat(trends_data["analysis_timestamp"])
                if (dt.datetime.now() - analysis_time).days > 7:
                    print(f"⚠️ Dane analizy dla {category} są przestarzałe ({analysis_time.date()})")
                    return {}
            except:
                pass
        
        return trends_data
        
    except Exception as e:
        print(f"❌ Błąd podczas pobierania najnowszej analizy: {e}")
        return {}

def get_analysis_for_date(category: str, report_date: str) -> Dict[str, Any]:
    """
    Pobiera analizę dla konkretnej daty.
    
    Args:
        category (str): Nazwa kategorii
        report_date (str): Data raportu
        
    Returns:
        Dict: Dane analizy lub pusty słownik
    """
    try:
        # Sprawdź czy istnieje plik z danymi wzrostu
        growth_file = growth_path(category, report_date)
        if not os.path.exists(growth_file):
            return {}
        
        # Wczytaj dane
        growth_data = load_json(growth_file)
        
        # Dodaj statystyki jeśli istnieją
        stats_file = stats_path(category, report_date)
        if os.path.exists(stats_file):
            stats_data = load_json(stats_file)
            growth_data["stats"] = stats_data.get("stats", {})
            growth_data["summary"] = stats_data.get("summary", {})
        
        return growth_data
        
    except Exception as e:
        print(f"❌ Błąd podczas pobierania analizy dla daty: {e}")
        return {}

def analyze_all_existing_csvs():
    """
    Analizuje wszystkie istniejące pliki CSV i zapisuje wyniki do trend_store.
    Użyteczne do przetworzenia już wygenerowanych plików CSV.
    """
    try:
        # Import CSVProcessor tutaj żeby uniknąć problemów z importami
        csv_processor = CSVProcessor()
        
        print("🔄 Rozpoczynam analizę wszystkich istniejących plików CSV...")
        
        # Kategorie do analizy
        categories = ["PODCAST", "MOTORYZACJA", "POLITYKA"]
        
        total_processed = 0
        total_success = 0
        
        for category in categories:
            print(f"\n📊 Analizuję kategorię: {category}")
            
            # Pobierz dostępne daty dla kategorii
            available_dates = csv_processor.get_available_dates(category)
            
            if not available_dates:
                print(f"⚠️ Brak plików CSV dla kategorii {category}")
                continue
            
            print(f"📅 Znaleziono {len(available_dates)} dat: {available_dates}")
            
            # Analizuj każdą datę
            for report_date in available_dates:
                try:
                    print(f"  🔍 Analizuję {category} {report_date}...")
                    
                    # Sprawdź czy analiza już istnieje
                    existing_analysis = get_analysis_for_date(category, report_date)
                    if existing_analysis and existing_analysis.get("videos"):
                        print(f"    ✅ Analiza już istnieje, pomijam")
                        continue
                    
                    # Wykonaj analizę
                    success = auto_analyze_and_save(category, report_date)
                    
                    if success:
                        print(f"    ✅ Pomyślnie przeanalizowano {category} {report_date}")
                        total_success += 1
                    else:
                        print(f"    ❌ Nie udało się przeanalizować {category} {report_date}")
                    
                    total_processed += 1
                    
                except Exception as e:
                    print(f"    ❌ Błąd podczas analizy {category} {report_date}: {e}")
                    total_processed += 1
        
        print(f"\n🎯 Analiza zakończona!")
        print(f"📊 Przetworzono: {total_processed} plików")
        print(f"✅ Pomyślnie: {total_success} plików")
        print(f"❌ Błędy: {total_processed - total_success} plików")
        
        return {
            "total_processed": total_processed,
            "total_success": total_success,
            "total_errors": total_processed - total_success
        }
        
    except Exception as e:
        print(f"❌ Błąd podczas analizy wszystkich CSV: {e}")
        return {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 1,
            "error": str(e)
        }

def force_reanalyze_category(category: str, report_date: str = None):
    """
    Wymusza ponowną analizę kategorii, nawet jeśli już istnieje.
    
    Args:
        category (str): Nazwa kategorii
        report_date (str): Data raportu (domyślnie dzisiejsza)
    """
    try:
        if report_date is None:
            report_date = dt.date.today().strftime("%Y-%m-%d")
        
        print(f"🔄 Wymuszam ponowną analizę dla {category} {report_date}")
        
        # Usuń istniejące pliki analizy
        try:
            if os.path.exists(growth_path(category, report_date)):
                os.remove(growth_path(category, report_date))
                print(f"🗑️ Usunięto istniejący plik wzrostu")
            
            if os.path.exists(stats_path(category, report_date)):
                os.remove(stats_path(category, report_date))
                print(f"🗑️ Usunięto istniejący plik statystyk")
        except Exception as e:
            print(f"⚠️ Nie udało się usunąć istniejących plików: {e}")
        
        # Wykonaj analizę
        success = auto_analyze_and_save(category, report_date)
        
        if success:
            print(f"✅ Pomyślnie przeanalizowano ponownie {category} {report_date}")
        else:
            print(f"❌ Nie udało się przeanalizować ponownie {category} {report_date}")
        
        return success
        
    except Exception as e:
        print(f"❌ Błąd podczas wymuszonej analizy: {e}")
        return False
