from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from ..youtube import YouTubeClient
from ..scheduler import TaskScheduler
from ..storage import CSVGenerator
from ..config import settings

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
        reports = []
        
        for file in os.listdir(settings.reports_path):
            if file.endswith('.csv'):
                file_path = settings.reports_path / file
                stats = os.stat(file_path)
                reports.append({
                    'filename': file,
                    'size': stats.st_size,
                    'created': stats.st_ctime,
                    'path': str(file_path)
                })
        
        return {"reports": sorted(reports, key=lambda x: x['created'], reverse=True)}
        
    except Exception as e:
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