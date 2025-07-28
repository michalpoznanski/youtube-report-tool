from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import pytz
from ..config import settings

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Klient YouTube Data API v3"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.quota_used = 0
        self.quota_limit = 10000  # Dzienny limit
        
    def _extract_channel_id(self, url: str) -> Optional[str]:
        """Wyciąga ID kanału z różnych formatów URL"""
        import re
        
        # Sprawdź czy URL zawiera watch?v= (link do filmu)
        if 'watch?v=' in url:
            raise ValueError("To jest link do filmu, nie do kanału. Użyj linku do kanału YouTube.")
        
        # Sprawdź czy URL zawiera @handle
        if '@' in url:
            # Wyciągnij handle z URL
            handle_match = re.search(r'youtube\.com/@([a-zA-Z0-9_-]+)', url)
            if handle_match:
                return f"@{handle_match.group(1)}"
            else:
                raise ValueError("Nieprawidłowy format URL z handle. Użyj: https://www.youtube.com/@NazwaKanału")
        
        # Sprawdź inne formaty URL
        patterns = [
            r'(?:youtube\.com/channel/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/c/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/user/)([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Nieprawidłowy URL kanału YouTube. Użyj linku do kanału zawierającego @handle.")
    
    async def get_channel_info(self, channel_url: str) -> Dict:
        """Pobiera informacje o kanale"""
        try:
            channel_id = self._extract_channel_id(channel_url)
            
            # Sprawdź czy to handle (@username)
            if channel_id.startswith('@'):
                handle = channel_id[1:]  # Usuń @ z początku
                logger.info(f"Wyszukiwanie kanału po handle: {handle}")
                
                # Wyszukaj kanał po handle
                request = self.service.search().list(
                    part='snippet',
                    q=handle,
                    type='channel',
                    maxResults=1
                )
                response = request.execute()
                self.quota_used += 100  # search.list = 100 quota
                
                # Sprawdź czy znaleziono kanał
                if 'items' not in response or len(response['items']) == 0:
                    logger.error(f"Nie znaleziono kanału dla handle: {handle}")
                    logger.error(f"Odpowiedź API: {response}")
                    raise ValueError(f"Nie znaleziono kanału YouTube dla: {handle}")
                
                # Pobierz channelId z wyniku wyszukiwania
                channel_id = response['items'][0]['snippet']['channelId']
                logger.info(f"Znaleziono channelId: {channel_id} dla handle: {handle}")
            
            # Pobierz szczegóły kanału
            request = self.service.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            self.quota_used += 1  # channels.list = 1 quota
            
            # Sprawdź czy znaleziono kanał
            if 'items' not in response or len(response['items']) == 0:
                logger.error(f"Nie znaleziono szczegółów kanału dla ID: {channel_id}")
                logger.error(f"Odpowiedź API: {response}")
                raise ValueError("Nie znaleziono kanału YouTube")
            
            channel = response['items'][0]
            return {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'view_count': int(channel['statistics'].get('viewCount', 0)),
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'published_at': channel['snippet']['publishedAt']
            }
            
        except HttpError as e:
            logger.error(f"Błąd YouTube API: {e}")
            logger.error(f"Szczegóły błędu: {e.resp.status} {e.content}")
            raise ValueError(f"Błąd YouTube API: {e}")
        except ValueError:
            # Przekaż błędy walidacji bez zmian
            raise
        except Exception as e:
            logger.error(f"Błąd podczas pobierania informacji o kanale: {e}")
            raise ValueError(f"Błąd podczas pobierania informacji o kanale: {e}")
    
    async def get_channel_videos(self, channel_id: str, days_back: int = 3) -> List[Dict]:
        """Pobiera filmy z kanału z ostatnich N dni"""
        try:
            # Oblicz datę początkową (offset-aware)
            end_date = datetime.now(pytz.utc)
            start_date = end_date - timedelta(days=days_back)
            
            # Pobierz playlistę uploadów kanału
            request = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            self.quota_used += 1  # channels.list = 1 quota
            
            if 'items' not in response or len(response['items']) == 0:
                logger.error(f"Nie znaleziono kanału dla ID: {channel_id}")
                return []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Pobierz filmy z playlisty
            videos = []
            next_page_token = None
            
            while True:
                request = self.service.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                self.quota_used += 1  # playlistItems.list = 1 quota
                
                if 'items' not in response:
                    logger.error(f"Nieprawidłowa odpowiedź API dla playlisty: {response}")
                    break
                
                for item in response['items']:
                    video_id = item['contentDetails']['videoId']
                    published_at = datetime.fromisoformat(
                        item['snippet']['publishedAt'].replace('Z', '+00:00')
                    )
                    
                    # Upewnij się, że published_at ma strefę czasową UTC
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=pytz.utc)
                    
                    # Sprawdź czy film jest z ostatnich N dni
                    if published_at >= start_date:
                        # Pobierz szczegóły filmu
                        video_details = await self._get_video_details(video_id)
                        if video_details:
                            videos.append(video_details)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except HttpError as e:
            logger.error(f"Błąd YouTube API: {e}")
            raise
        except Exception as e:
            logger.error(f"Błąd podczas pobierania filmów: {e}")
            raise
    
    async def _get_video_details(self, video_id: str) -> Optional[Dict]:
        """Pobiera szczegóły filmu"""
        try:
            request = self.service.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            self.quota_used += 1  # videos.list = 1 quota
            
            if 'items' not in response or len(response['items']) == 0:
                logger.error(f"Nie znaleziono filmu dla ID: {video_id}")
                return None
            
            video = response['items'][0]
            return {
                'id': video['id'],
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'published_at': video['snippet']['publishedAt'],
                'tags': video['snippet'].get('tags', []),
                'category_id': video['snippet']['categoryId'],
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'favorite_count': int(video['statistics'].get('favoriteCount', 0)),
                'duration': video['contentDetails']['duration'],
                'definition': video['contentDetails']['definition'],
                'caption': video['contentDetails']['caption'],
                'licensed_content': video['contentDetails']['licensedContent'],
                'thumbnail': video['snippet']['thumbnails']['default']['url']
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szczegółów filmu {video_id}: {e}")
            return None
    
    def get_quota_usage(self) -> Dict:
        """Zwraca informacje o zużyciu quota"""
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.quota_limit - self.quota_used,
            'percentage': (self.quota_used / self.quota_limit) * 100
        }
    
    def reset_quota(self):
        """Resetuje licznik quota (wywoływane codziennie)"""
        self.quota_used = 0
        logger.info("Quota zostało zresetowane") 