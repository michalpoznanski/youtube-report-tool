from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from typing import Dict, List
from ..config import settings
from ..youtube import YouTubeClient
from ..storage import CSVGenerator
from ..storage.state_manager import StateManager

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler zadań z APScheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.state_manager = StateManager()  # Zarządza trwałymi danymi
        self.youtube_client = YouTubeClient(settings.youtube_api_key, self.state_manager)
        self.csv_generator = CSVGenerator()
    
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
            
            # Reset quota (tylko raz dziennie)
            self.state_manager.reset_quota()
            
            # Pobierz dane ze wszystkich kanałów
            all_videos = {}
            
            for category, channels in self.state_manager.get_channels().items():
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
                
                # Zapisz aktualne zużycie quota po wygenerowaniu raportów
                try:
                    current_quota = self.youtube_client.get_quota_usage()
                    self.state_manager.persist_quota(current_quota['used'])
                    logger.info(f"Zapisano quota po wygenerowaniu raportów: {current_quota['used']}")
                except Exception as e:
                    logger.error(f"Błąd podczas zapisywania quota: {e}")
            
            # Log quota usage
            quota_state = self.state_manager.get_quota_state()
            logger.info(f"Zużycie quota: {quota_state['used']}/10000 ({quota_state['used']/100:.1f}%)")
            
            logger.info("Codzienne zadanie raportowania zakończone")
            
        except Exception as e:
            logger.error(f"Błąd podczas wykonywania codziennego zadania: {e}")
    
    def add_channel(self, channel_data: Dict, category: str = "general"):
        """Dodaje kanał do monitorowania"""
        return self.state_manager.add_channel(channel_data, category)
    
    def remove_channel(self, channel_id: str, category: str = "general"):
        """Usuwa kanał z monitorowania"""
        return self.state_manager.remove_channel(channel_id, category)
    
    def get_channels(self) -> Dict[str, List[Dict]]:
        """Zwraca listę wszystkich kanałów"""
        return self.state_manager.get_channels()
    
    def get_status(self) -> Dict:
        """Zwraca status schedulera"""
        channels = self.state_manager.get_channels()
        return {
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'channels_count': sum(len(channels) for channels in channels.values()),
            'categories': list(channels.keys()),
            'next_run': self.scheduler.get_job('daily_report').next_run_time.isoformat() if self.scheduler.get_job('daily_report') else None
        }
    
    async def add_channel(self, channel_url: str, category: str = "general"):
        """Dodaje kanał do monitorowania"""
        try:
            # Pobierz informacje o kanale
            channel_info = await self.youtube_client.get_channel_info(channel_url)
            
            # Dodaj do state manager
            self.state_manager.add_channel(channel_info, category)
            
            logger.info(f"Dodano kanał: {channel_info['title']} do kategorii {category}")
            return channel_info
                
        except Exception as e:
            logger.error(f"Błąd podczas dodawania kanału: {e}")
            raise
    
    async def get_channel_videos(self, channel_id: str, days_back: int = 3):
        """Pobiera filmy z kanału"""
        return await self.youtube_client.get_channel_videos(channel_id, days_back)
    
    def get_quota_usage(self) -> Dict:
        """Zwraca informacje o zużyciu quota"""
        return self.youtube_client.get_quota_usage()
    
    def get_cache_stats(self) -> Dict:
        """Zwraca statystyki cache"""
        return self.youtube_client.get_cache_stats()
    
    def cleanup_cache(self) -> int:
        """Czyści przestarzały cache"""
        return self.youtube_client.cleanup_cache()

    def add_category(self, category_name: str) -> Dict:
        """Dodaje nową kategorię"""
        return self.state_manager.add_category(category_name)

    def remove_category(self, category_name: str, force: bool = False) -> Dict:
        """Usuwa kategorię"""
        return self.state_manager.remove_category(category_name, force)

    def get_categories(self) -> List[Dict]:
        """Zwraca listę kategorii"""
        return self.state_manager.get_categories() 