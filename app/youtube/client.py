from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
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
        
        patterns = [
            r'(?:youtube\.com/channel/|youtube\.com/c/|youtube\.com/@)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/user/)([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_channel_info(self, channel_url: str) -> Dict:
        """Pobiera informacje o kanale"""
        try:
            channel_id = self._extract_channel_id(channel_url)
            if not channel_id:
                raise ValueError("Nieprawidłowy URL kanału YouTube")
            
            # Sprawdź czy to handle (@username)
            if channel_url.startswith('@'):
                request = self.service.search().list(
                    part='snippet',
                    q=channel_url,
                    type='channel',
                    maxResults=1
                )
                response = request.execute()
                if response['items']:
                    channel_id = response['items'][0]['snippet']['channelId']
                    self.quota_used += 100  # search.list = 100 quota
            
            # Pobierz szczegóły kanału
            request = self.service.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            self.quota_used += 1  # channels.list = 1 quota
            
            if not response['items']:
                raise ValueError("Kanał nie został znaleziony")
            
            channel = response['items'][0]
            return {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                'video_count': channel['statistics'].get('videoCount', 0),
                'view_count': channel['statistics'].get('viewCount', 0),
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'published_at': channel['snippet']['publishedAt']
            }
            
        except HttpError as e:
            logger.error(f"Błąd YouTube API: {e}")
            raise
        except Exception as e:
            logger.error(f"Błąd podczas pobierania informacji o kanale: {e}")
            raise
    
    async def get_channel_videos(self, channel_id: str, days_back: int = 3) -> List[Dict]:
        """Pobiera filmy z kanału z ostatnich N dni"""
        try:
            # Oblicz datę początkową
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Pobierz playlistę uploadów kanału
            request = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            self.quota_used += 1  # channels.list = 1 quota
            
            if not response['items']:
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
                
                for item in response['items']:
                    video_id = item['contentDetails']['videoId']
                    published_at = datetime.fromisoformat(
                        item['snippet']['publishedAt'].replace('Z', '+00:00')
                    )
                    
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
            
            if not response['items']:
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