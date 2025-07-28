from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from ..youtube import YouTubeClient
from ..scheduler import TaskScheduler
from ..storage import CSVGenerator
from ..config import settings
import json

logger = logging.getLogger(__name__)

router = APIRouter()
# Używamy globalnej instancji z main.py
task_scheduler = None

def set_task_scheduler(scheduler_instance):
    """Ustawia globalną instancję schedulera"""
    global task_scheduler
    task_scheduler = scheduler_instance


# Pydantic models
class ChannelRequest(BaseModel):
    url: str
    category: str = "general"


class ChannelResponse(BaseModel):
    id: str
    title: str
    description: str
    subscriber_count: int
    video_count: int
    view_count: int
    thumbnail: str
    category: str


class ReportRequest(BaseModel):
    category: Optional[str] = None
    days_back: int = 3


class StatusResponse(BaseModel):
    scheduler_running: bool
    channels_count: int
    categories: List[str]
    quota_usage: Dict
    next_report: Optional[str]
    cache_stats: Optional[Dict] = None


@router.post("/channels", response_model=ChannelResponse)
async def add_channel(channel_request: ChannelRequest):
    """Dodaje kanał YouTube do monitorowania"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
            
        # Dodaj kanał przez scheduler
        channel_info = await task_scheduler.add_channel(channel_request.url, channel_request.category)
        
        # Dodaj kategorię do odpowiedzi
        channel_info['category'] = channel_request.category
        
        logger.info(f"Dodano kanał: {channel_info['title']} do kategorii {channel_request.category}")
        return channel_info
        
    except Exception as e:
        logger.error(f"Błąd podczas dodawania kanału: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/channels", response_model=Dict[str, List[ChannelResponse]])
async def get_channels():
    """Zwraca listę wszystkich kanałów"""
    try:
        if not task_scheduler:
            return {}
        channels = task_scheduler.get_channels()
        return channels
    except Exception as e:
        logger.error(f"Błąd podczas pobierania kanałów: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/channels/{channel_id}")
async def remove_channel(channel_id: str, category: str = "general"):
    """Usuwa kanał z monitorowania"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        task_scheduler.remove_channel(channel_id, category)
        return {"message": f"Kanał {channel_id} został usunięty z kategorii {category}"}
    except Exception as e:
        logger.error(f"Błąd podczas usuwania kanału: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(report_request: ReportRequest):
    """Generuje raport CSV dla określonej kategorii"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
            
        channels = task_scheduler.get_channels()
        
        if report_request.category and report_request.category not in channels:
            raise HTTPException(status_code=404, detail=f"Kategoria {report_request.category} nie istnieje")
        
        all_videos = {}
        
        # Pobierz dane z kanałów
        target_categories = [report_request.category] if report_request.category else channels.keys()
        
        for category in target_categories:
            if category in channels:
                category_videos = []
                
                for channel in channels[category]:
                    try:
                        videos = await task_scheduler.get_channel_videos(
                            channel['id'], 
                            report_request.days_back
                        )
                        
                        # Dodaj informacje o kanale
                        for video in videos:
                            video['channel_title'] = channel['title']
                            video['channel_id'] = channel['id']
                        
                        category_videos.extend(videos)
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas pobierania filmów z kanału {channel['title']}: {e}")
                
                if category_videos:
                    all_videos[category] = category_videos
        
        if not all_videos:
            raise HTTPException(status_code=404, detail="Brak danych do wygenerowania raportu")
        
        # Generuj CSV
        csv_generator = CSVGenerator()
        
        if report_request.category:
            # Raport dla jednej kategorii
            csv_path = csv_generator.generate_csv(all_videos[report_request.category], report_request.category)
        else:
            # Raport podsumowujący
            csv_path = csv_generator.generate_summary_csv(all_videos)
        
        return FileResponse(
            path=csv_path,
            filename=csv_path.split('/')[-1],
            media_type='text/csv'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas generowania raportu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/list")
async def list_reports():
    """Zwraca listę dostępnych raportów"""
    try:
        import os
        from datetime import datetime
        
        reports = []
        reports_dir = settings.reports_path
        
        print(f"📂 Szukanie raportów w: {reports_dir.absolute()}")
        logger.info(f"Szukanie raportów w: {reports_dir.absolute()}")
        
        # Sprawdź czy katalog istnieje
        if not reports_dir.exists():
            print(f"⚠️ Katalog raportów nie istnieje: {reports_dir.absolute()}")
            logger.warning(f"Katalog raportów nie istnieje: {reports_dir.absolute()}")
            # Utwórz katalog
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Utworzono katalog raportów: {reports_dir.absolute()}")
            logger.info(f"Utworzono katalog raportów: {reports_dir.absolute()}")
        
        # Listuj pliki CSV
        csv_files = list(reports_dir.glob("*.csv"))
        print(f"📄 Znaleziono {len(csv_files)} plików CSV")
        logger.info(f"Znaleziono {len(csv_files)} plików CSV")
        
        for file_path in csv_files:
            try:
                stats = os.stat(file_path)
                reports.append({
                    'filename': file_path.name,
                    'size': stats.st_size,
                    'created': stats.st_ctime,
                    'created_date': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    'path': str(file_path.absolute())
                })
                print(f"   📄 {file_path.name} ({stats.st_size} bytes)")
            except Exception as e:
                print(f"   ❌ Błąd podczas czytania {file_path.name}: {e}")
                logger.error(f"Błąd podczas czytania {file_path.name}: {e}")
        
        # Sortuj po dacie utworzenia (najnowsze pierwsze)
        sorted_reports = sorted(reports, key=lambda x: x['created'], reverse=True)
        
        print(f"✅ Zwracam {len(sorted_reports)} raportów")
        logger.info(f"Zwracam {len(sorted_reports)} raportów")
        
        return {
            "reports": sorted_reports,
            "total_count": len(sorted_reports),
            "reports_directory": str(reports_dir.absolute())
        }
        
    except Exception as e:
        print(f"❌ Błąd podczas listowania raportów: {e}")
        logger.error(f"Błąd podczas listowania raportów: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """Pobiera konkretny raport"""
    try:
        file_path = settings.reports_path / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Raport nie istnieje")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='text/csv'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas pobierania raportu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Zwraca status systemu"""
    try:
        if not task_scheduler:
            return StatusResponse(
                scheduler_running=False,
                channels_count=0,
                categories=[],
                quota_usage=task_scheduler.get_quota_usage(),
                next_report=None
            )
            
        scheduler_status = task_scheduler.get_status()
        quota_info = task_scheduler.get_quota_usage()
        
        # Pobierz statystyki cache
        cache_stats = task_scheduler.get_cache_stats()
        
        return StatusResponse(
            scheduler_running=scheduler_status['running'],
            channels_count=scheduler_status['channels_count'],
            categories=scheduler_status['categories'],
            quota_usage=quota_info,
            next_report=scheduler_status['next_run'],
            cache_stats=cache_stats
        )
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statusu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/start")
async def start_scheduler():
    """Uruchamia scheduler"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        task_scheduler.start()
        return {"message": "Scheduler uruchomiony"}
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania schedulera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Zatrzymuje scheduler"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        task_scheduler.stop()
        return {"message": "Scheduler zatrzymany"}
    except Exception as e:
        logger.error(f"Błąd podczas zatrzymywania schedulera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Zwraca statystyki cache"""
    try:
        cache_stats = task_scheduler.get_cache_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statystyk cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup")
async def cleanup_cache():
    """Czyści przestarzały cache"""
    try:
        cleaned_count = task_scheduler.cleanup_cache()
        return {"message": f"Usunięto {cleaned_count} przestarzałych wpisów z cache"}
    except Exception as e:
        logger.error(f"Błąd podczas czyszczenia cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/clear")
async def clear_all_data():
    """Czyści wszystkie dane (dla testów)"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        
        task_scheduler.state_manager.clear_all_data()
        return {"message": "Wszystkie dane zostały wyczyszczone"}
    except Exception as e:
        logger.error(f"Błąd podczas czyszczenia danych: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/stats")
async def get_data_stats():
    """Zwraca statystyki danych"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        
        stats = task_scheduler.state_manager.get_data_stats()
        return stats
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statystyk danych: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/json")
async def debug_json_files():
    """Debug endpoint - pokazuje zawartość plików JSON"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        
        state_manager = task_scheduler.state_manager
        
        # Sprawdź czy pliki istnieją
        channels_exists = state_manager.channels_file.exists()
        quota_exists = state_manager.quota_file.exists()
        system_exists = state_manager.system_state_file.exists()
        
        # Wczytaj zawartość plików
        channels_content = None
        quota_content = None
        system_content = None
        
        if channels_exists:
            try:
                with open(state_manager.channels_file, 'r', encoding='utf-8') as f:
                    channels_content = json.load(f)
            except Exception as e:
                channels_content = f"Błąd odczytu: {e}"
        
        if quota_exists:
            try:
                with open(state_manager.quota_file, 'r', encoding='utf-8') as f:
                    quota_content = json.load(f)
            except Exception as e:
                quota_content = f"Błąd odczytu: {e}"
        
        if system_exists:
            try:
                with open(state_manager.system_state_file, 'r', encoding='utf-8') as f:
                    system_content = json.load(f)
            except Exception as e:
                system_content = f"Błąd odczytu: {e}"
        
        return {
            "data_directory": str(state_manager.data_dir.absolute()),
            "files": {
                "channels.json": {
                    "exists": channels_exists,
                    "path": str(state_manager.channels_file.absolute()),
                    "content": channels_content
                },
                "quota_state.json": {
                    "exists": quota_exists,
                    "path": str(state_manager.quota_file.absolute()),
                    "content": quota_content
                },
                "system_state.json": {
                    "exists": system_exists,
                    "path": str(state_manager.system_state_file.absolute()),
                    "content": system_content
                }
            },
            "memory_state": {
                "channels_count": sum(len(channels) for channels in state_manager.channels_data.values()),
                "quota_used": state_manager.quota_state.get('used', 0),
                "system_startup": state_manager.system_state.get('last_startup')
            }
        }
    except Exception as e:
        logger.error(f"Błąd podczas debugowania plików JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/debug/reports")
async def debug_reports():
    """Debug endpoint - pokazuje informacje o katalogu raportów"""
    try:
        import os
        from datetime import datetime
        
        reports_dir = settings.reports_path
        
        # Sprawdź czy katalog istnieje
        exists = reports_dir.exists()
        absolute_path = str(reports_dir.absolute())
        
        # Sprawdź uprawnienia
        can_write = False
        can_read = False
        if exists:
            try:
                test_file = reports_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                can_write = True
            except Exception:
                can_write = False
            
            try:
                list(reports_dir.iterdir())
                can_read = True
            except Exception:
                can_read = False
        
        # Listuj pliki
        csv_files = []
        if exists and can_read:
            for file_path in reports_dir.glob("*.csv"):
                try:
                    stats = os.stat(file_path)
                    csv_files.append({
                        'name': file_path.name,
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        'path': str(file_path.absolute())
                    })
                except Exception as e:
                    csv_files.append({
                        'name': file_path.name,
                        'error': str(e)
                    })
        
        return {
            "reports_directory": {
                "path": absolute_path,
                "exists": exists,
                "can_write": can_write,
                "can_read": can_read
            },
            "csv_files": csv_files,
            "total_csv_files": len(csv_files),
            "railway_volume_path": os.getenv("RAILWAY_VOLUME_PATH", "Not set")
        }
        
    except Exception as e:
        logger.error(f"Błąd podczas debugowania raportów: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/debug/env")
async def debug_environment():
    """Debug endpoint - pokazuje zmienne środowiskowe"""
    try:
        import os
        
        env_vars = {
            "RAILWAY_VOLUME_PATH": os.getenv("RAILWAY_VOLUME_PATH", "Not set"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not set"),
            "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID", "Not set"),
            "RAILWAY_SERVICE_ID": os.getenv("RAILWAY_SERVICE_ID", "Not set"),
            "PWD": os.getcwd(),
            "HOME": os.getenv("HOME", "Not set"),
            "USER": os.getenv("USER", "Not set"),
        }
        
        return {
            "environment_variables": env_vars,
            "current_working_directory": os.getcwd(),
            "data_directory_exists": os.path.exists("/app/data"),
            "data_directory_writable": os.access("/app/data", os.W_OK) if os.path.exists("/app/data") else False,
            "reports_directory_exists": os.path.exists("/app/reports"),
            "reports_directory_writable": os.access("/app/reports", os.W_OK) if os.path.exists("/app/reports") else False,
        }
        
    except Exception as e:
        logger.error(f"Błąd podczas debugowania zmiennych środowiskowych: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.post("/debug/test-persistence")
async def test_data_persistence():
    """Test endpoint - sprawdza trwałość danych"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        
        state_manager = task_scheduler.state_manager
        
        # Dodaj testowy kanał
        test_channel = {
            "id": "TEST_CHANNEL_123",
            "title": "Test Channel",
            "description": "Test channel for persistence",
            "subscriber_count": 1000,
            "video_count": 50,
            "view_count": 100000,
            "thumbnail": "https://example.com/thumb.jpg",
            "published_at": "2020-01-01T00:00:00Z"
        }
        
        # Zapisz kanał
        state_manager.add_channel(test_channel, "test_persistence")
        
        # Sprawdź czy został zapisany
        channels = state_manager.get_channels()
        test_channels = channels.get("test_persistence", [])
        
        # Sprawdź czy plik istnieje
        channels_file_exists = state_manager.channels_file.exists()
        
        return {
            "test_channel_added": len(test_channels) > 0,
            "test_channel_id": test_channels[0]["id"] if test_channels else None,
            "channels_file_exists": channels_file_exists,
            "channels_file_path": str(state_manager.channels_file.absolute()),
            "total_channels": sum(len(channels) for channels in channels.values()),
            "message": "Test kanał został dodany. Sprawdź czy przetrwa restart Railway."
        }
        
    except Exception as e:
        logger.error(f"Błąd podczas testowania trwałości danych: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/debug/check-persistence")
async def check_data_persistence():
    """Sprawdza czy dane są trwałe po restarcie"""
    try:
        if not task_scheduler:
            raise HTTPException(status_code=500, detail="Scheduler nie jest dostępny")
        
        state_manager = task_scheduler.state_manager
        
        # Sprawdź czy pliki istnieją
        channels_exists = state_manager.channels_file.exists()
        quota_exists = state_manager.quota_file.exists()
        system_exists = state_manager.system_state_file.exists()
        
        # Sprawdź dane w pamięci
        channels_count = sum(len(channels) for channels in state_manager.channels_data.values())
        quota_used = state_manager.quota_state.get('used', 0)
        system_startup = state_manager.system_state.get('last_startup')
        
        # Sprawdź czy są testowe kanały
        test_channels = state_manager.channels_data.get("test_persistence", [])
        has_test_channel = any(channel.get("id") == "TEST_CHANNEL_123" for channel in test_channels)
        
        return {
            "files_exist": {
                "channels.json": channels_exists,
                "quota_state.json": quota_exists,
                "system_state.json": system_exists
            },
            "memory_data": {
                "channels_count": channels_count,
                "quota_used": quota_used,
                "system_startup": system_startup
            },
            "test_persistence": {
                "has_test_channel": has_test_channel,
                "test_channels_count": len(test_channels)
            },
            "data_directory": str(state_manager.data_dir.absolute()),
            "railway_volume_path": os.getenv("RAILWAY_VOLUME_PATH", "Not set")
        }
        
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania trwałości danych: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 