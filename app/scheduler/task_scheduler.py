from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from typing import Dict, List
from ..config import settings
from ..youtube import YouTubeClient
from ..storage import CSVGenerator

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler zadań z APScheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.youtube_client = YouTubeClient(settings.youtube_api_key)
        self.csv_generator = CSVGenerator()
        self.channels_data = {}  # Przechowuje dane kanałów
    
    def start(self):
        """Uruchamia scheduler"""
        try:
            # Dodaj zadanie codziennego raportu
            self.scheduler.add_job(
                func=self.daily_report_task,
                trigger=CronTrigger(
                    hour=settings.scheduler_hour,
                    minute=settings.scheduler_minute
                ),
                id='daily_report',
                name='Codzienny raport YouTube',
                replace_existing=True
            )
            
            # Uruchom scheduler
            self.scheduler.start()
            logger.info(f"Scheduler uruchomiony - raporty codziennie o {settings.scheduler_hour}:{settings.scheduler_minute:02d}")
            
        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania schedulera: {e}")
            raise
    
    def stop(self):
        """Zatrzymuje scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler zatrzymany")
    
    async def daily_report_task(self):
        """Codzienne zadanie generowania raportów"""
        try:
            logger.info("Rozpoczęcie codziennego zadania raportowania")
            
            # Reset quota
            self.youtube_client.reset_quota()
            
            # Pobierz dane ze wszystkich kanałów
            all_videos = {}
            
            for category, channels in self.channels_data.items():
                category_videos = []
                
                for channel in channels:
                    try:
                        videos = await self.youtube_client.get_channel_videos(
                            channel['id'], 
                            settings.days_back
                        )
                        
                        # Dodaj informacje o kanale do każdego filmu
                        for video in videos:
                            video['channel_title'] = channel['title']
                            video['channel_id'] = channel['id']
                        
                        category_videos.extend(videos)
                        logger.info(f"Pobrano {len(videos)} filmów z kanału {channel['title']}")
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas pobierania filmów z kanału {channel['title']}: {e}")
                
                if category_videos:
                    all_videos[category] = category_videos
            
            # Generuj raporty CSV
            if all_videos:
                # Raport dla każdej kategorii
                for category, videos in all_videos.items():
                    try:
                        csv_path = self.csv_generator.generate_csv(videos, category)
                        logger.info(f"Wygenerowano raport dla kategorii {category}: {csv_path}")
                    except Exception as e:
                        logger.error(f"Błąd podczas generowania raportu dla kategorii {category}: {e}")
                
                # Raport podsumowujący
                try:
                    summary_path = self.csv_generator.generate_summary_csv(all_videos)
                    logger.info(f"Wygenerowano raport podsumowujący: {summary_path}")
                except Exception as e:
                    logger.error(f"Błąd podczas generowania raportu podsumowującego: {e}")
            
            # Log quota usage
            quota_info = self.youtube_client.get_quota_usage()
            logger.info(f"Zużycie quota: {quota_info['used']}/{quota_info['limit']} ({quota_info['percentage']:.1f}%)")
            
            logger.info("Codzienne zadanie raportowania zakończone")
            
        except Exception as e:
            logger.error(f"Błąd podczas wykonywania codziennego zadania: {e}")
    
    def add_channel(self, channel_data: Dict, category: str = "general"):
        """Dodaje kanał do monitorowania"""
        if category not in self.channels_data:
            self.channels_data[category] = []
        
        # Sprawdź czy kanał już istnieje
        existing_ids = [ch['id'] for ch in self.channels_data[category]]
        if channel_data['id'] not in existing_ids:
            self.channels_data[category].append(channel_data)
            logger.info(f"Dodano kanał {channel_data['title']} do kategorii {category}")
        else:
            logger.warning(f"Kanał {channel_data['title']} już istnieje w kategorii {category}")
    
    def remove_channel(self, channel_id: str, category: str = "general"):
        """Usuwa kanał z monitorowania"""
        if category in self.channels_data:
            self.channels_data[category] = [
                ch for ch in self.channels_data[category] 
                if ch['id'] != channel_id
            ]
            logger.info(f"Usunięto kanał {channel_id} z kategorii {category}")
    
    def get_channels(self) -> Dict[str, List[Dict]]:
        """Zwraca listę wszystkich kanałów"""
        return self.channels_data
    
    def get_status(self) -> Dict:
        """Zwraca status schedulera"""
        return {
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'channels_count': sum(len(channels) for channels in self.channels_data.values()),
            'categories': list(self.channels_data.keys()),
            'next_run': self.scheduler.get_job('daily_report').next_run_time.isoformat() if self.scheduler.get_job('daily_report') else None
        } 