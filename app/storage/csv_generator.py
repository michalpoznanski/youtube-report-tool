import pandas as pd
from typing import List, Dict
from datetime import datetime
import pytz
import logging
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)


class CSVGenerator:
    """Generator plików CSV z danymi YouTube"""
    
    def __init__(self):
        self.columns = [
            'Channel_Name',
            'Channel_ID',
            'Date_of_Publishing',
            'Hour_GMT2',
            'Title',
            'Description',
            'Tags',
            'Video_Type',
            'View_Count',
            'Like_Count',
            'Comment_Count',
            'Favorite_Count',
            'Definition',
            'Has_Captions',
            'Licensed_Content',
            'Topic_Categories',
            'Names_Extracted',
            'Video_ID',
            'Duration',
            'Thumbnail_URL'
        ]
    
    def generate_csv(self, videos_data: List[Dict], category: str = "general") -> str:
        """Generuje plik CSV z danymi filmów"""
        try:
            # Przygotuj dane
            rows = []
            for video in videos_data:
                # Wyciągnij nazwiska
                from ..analysis import NameExtractor
                extractor = NameExtractor()
                names = extractor.extract_from_video_data(video)
                
                # Określ typ filmu (shorts vs long)
                video_type = self._determine_video_type(video.get('duration', ''), video.get('id', ''), video.get('url', ''))
                
                # Przygotuj datę (offset-aware)
                published_at = datetime.fromisoformat(
                    video['published_at'].replace('Z', '+00:00')
                )
                # Upewnij się, że ma strefę czasową UTC
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=pytz.utc)
                date_str = published_at.strftime('%Y-%m-%d')
                hour_str = published_at.strftime('%H:%M')
                
                row = {
                    'Channel_Name': video.get('channel_title', ''),
                    'Channel_ID': video.get('channel_id', ''),
                    'Date_of_Publishing': date_str,
                    'Hour_GMT2': hour_str,
                    'Title': video.get('title', ''),
                    'Description': video.get('description', ''),
                    'Tags': ', '.join(video.get('tags', [])),
                    'Video_Type': video_type,
                    'View_Count': video.get('view_count', 0),
                    'Like_Count': video.get('like_count', 0),
                    'Comment_Count': video.get('comment_count', 0),
                    'Favorite_Count': video.get('favorite_count', 0),
                    'Definition': video.get('definition', ''),
                    'Has_Captions': video.get('caption', ''),
                    'Licensed_Content': video.get('licensed_content', False),
                    'Topic_Categories': video.get('category_id', ''),
                    'Names_Extracted': ', '.join(names),
                    'Video_ID': video.get('id', ''),
                    'Duration': video.get('duration', ''),
                    'Thumbnail_URL': video.get('thumbnail', '')
                }
                rows.append(row)
            
            # Utwórz DataFrame
            df = pd.DataFrame(rows, columns=self.columns)
            
            # Generuj nazwę pliku
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{category}_{timestamp}.csv"
            filepath = settings.reports_path / filename
            
            # Zapisz CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Wygenerowano CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania CSV: {e}")
            raise
    
    def _determine_video_type(self, duration: str, video_id: str = None, video_url: str = None) -> str:
        """Określa typ filmu na podstawie długości i URL"""
        if not duration:
            return "unknown"
        
        # Konwertuj ISO 8601 duration na sekundy
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Sprawdź czy URL zawiera "/shorts/"
            is_shorts_url = False
            if video_url and "/shorts/" in video_url:
                is_shorts_url = True
            elif video_id:
                # Sprawdź czy film może być dostępny jako shorts
                # YouTube Shorts URL format: https://www.youtube.com/shorts/VIDEO_ID
                shorts_url = f"https://www.youtube.com/shorts/{video_id}"
                # Dla uproszczenia, jeśli duration < 60s, uznajemy za potencjalny shorts
                if total_seconds <= 60:
                    is_shorts_url = True
            
            # Logika: Jeśli duration < 60s i URL zawiera "/shorts/" to SHORTS, inaczej LONG
            if total_seconds <= 60 and is_shorts_url:
                return "shorts"
            else:
                return "long"
        
        return "unknown"
    
    def generate_summary_csv(self, all_data: Dict[str, List[Dict]]) -> str:
        """Generuje podsumowanie CSV ze wszystkich kategorii"""
        try:
            all_rows = []
            
            for category, videos in all_data.items():
                for video in videos:
                    # Dodaj kategorię do danych
                    video['category'] = category
                    all_rows.append(video)
            
            # Generuj nazwę pliku
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"summary_{timestamp}.csv"
            filepath = settings.reports_path / filename
            
            # Utwórz DataFrame i zapisz
            df = pd.DataFrame(all_rows)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Wygenerowano podsumowanie CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania podsumowania CSV: {e}")
            raise 