try:
    import asyncio
    import logging
    from typing import Dict, List, Optional, Any
    from datetime import datetime, timedelta
    import json
    from pathlib import Path
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import time
    import re
    import pytz
    
    print("✅ Wszystkie importy w YouTube client udane")
except ImportError as e:
    print(f"❌ Błąd importu w YouTube client: {e}")
    import traceback
    traceback.print_exc()
    raise

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Klient YouTube Data API v3"""
    
    def __init__(self, api_key: str, state_manager=None):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.quota_limit = 10000  # Dzienny limit
        self.state_manager = state_manager
        
        # Cache system
        self.video_cache = {}
        self.cache_file = Path("video_cache.json")
        self.load_cache()
        
    def load_cache(self):
        """Ładuje cache z pliku"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.video_cache = json.load(f)
                logger.info(f"Załadowano cache: {len(self.video_cache)} filmów")
            else:
                self.video_cache = {}
                logger.info("Utworzono nowy cache")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania cache: {e}")
            self.video_cache = {}
    
    def save_cache(self):
        """Zapisuje cache do pliku"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.video_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Zapisano cache: {len(self.video_cache)} filmów")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania cache: {e}")
    
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
        
        # Sprawdź format /channel/UC...
        channel_id_match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', url)
        if channel_id_match:
            return channel_id_match.group(1)
        
        # Sprawdź inne formaty URL
        patterns = [
            r'(?:youtube\.com/c/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/user/)([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Nieprawidłowy URL kanału YouTube. Użyj linku do kanału zawierającego @handle lub /channel/UC...")
    
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
                if self.state_manager:
                    self.state_manager.add_quota_used(100)  # search.list = 100 quota
                
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
            if self.state_manager:
                self.state_manager.add_quota_used(1)  # channels.list = 1 quota
            
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
                'published_at': channel['snippet']['publishedAt'],
                'url': channel_url  # Dodaj oryginalny URL
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
        """
        Pobiera filmy z kanału YouTube z ostatnich N dni.
        
        Args:
            channel_id: ID kanału YouTube
            days_back: Ile dni wstecz pobierać (domyślnie 3)
        
        Returns:
            Lista filmów z kanału
        """
        try:
            # Oblicz datę początkową (offset-aware)
            end_date = datetime.now(pytz.utc)
            start_date = end_date - timedelta(days=days_back)
            
            print(f"📅 Pobieranie filmów z ostatnich {days_back} dni (od {start_date} do {end_date})")
            
            # Pobierz playlistę uploadów kanału
            request = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            if self.state_manager:
                self.state_manager.add_quota_used(1)  # channels.list = 1 quota
            
            if 'items' not in response or len(response['items']) == 0:
                logger.error(f"Nie znaleziono kanału dla ID: {channel_id}")
                return []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Pobierz filmy z playlisty
            videos = []
            video_ids = []  # Zbierz ID filmów do batch processing
            next_page_token = None
            total_checked = 0
            videos_in_range = 0
            
            # Pobierz więcej filmów aby znaleźć shorts
            max_pages = 5  # Zwiększ limit stron
            page_count = 0
            
            while page_count < max_pages:
                request = self.service.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                if self.state_manager:
                    self.state_manager.add_quota_used(1)  # playlistItems.list = 1 quota
                
                if 'items' not in response:
                    logger.error(f"Nieprawidłowa odpowiedź API dla playlisty: {response}")
                    break
                
                page_count += 1
                total_checked += len(response['items'])
                
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
                        # Zbierz ID filmów do batch processing
                        video_ids.append(video_id)
                        videos_in_range += 1
                
                print(f"📄 Strona {page_count}: sprawdzono {len(response['items'])} filmów, w zakresie: {videos_in_range}")
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            print(f"📊 Łącznie sprawdzono {total_checked} filmów, w zakresie czasowym: {videos_in_range}")
            
            # Pobierz szczegóły filmów za pomocą batch processing
            if video_ids:
                logger.info(f"Pobieranie szczegółów {len(video_ids)} filmów (batch)")
                video_details = await self._get_video_details_batch(video_ids)
                videos.extend(video_details)
                
                # Sprawdź typy filmów
                shorts_count = sum(1 for v in video_details if v.get('duration', '') and self._is_short_video(v.get('duration', '')))
                long_count = len(video_details) - shorts_count
                print(f"🎬 Znaleziono: {shorts_count} shorts, {long_count} long form")
            else:
                print("⚠️ Nie znaleziono filmów w zakresie czasowym")
            
            return videos
            
        except HttpError as e:
            logger.error(f"Błąd YouTube API: {e}")
            raise
        except Exception as e:
            logger.error(f"Błąd podczas pobierania filmów: {e}")
            raise
    
    async def _get_video_details(self, video_id: str) -> Optional[Dict]:
        """Pobiera szczegóły filmu z cache"""
        # Sprawdź cache (ważny przez 24h)
        if video_id in self.video_cache:
            cache_data = self.video_cache[video_id]
            cache_age = datetime.now().timestamp() - cache_data['timestamp']
            
            # Cache ważny przez 24h (86400 sekund)
            if cache_age < 86400:
                logger.debug(f"Pobrano z cache: {video_id}")
                return cache_data['data']
            else:
                # Usuń przestarzały cache
                del self.video_cache[video_id]
                logger.debug(f"Usunięto przestarzały cache: {video_id}")
        
        # Pobierz z API
        try:
            request = self.service.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            if self.state_manager:
                self.state_manager.add_quota_used(1)  # videos.list = 1 quota
            
            if 'items' not in response or len(response['items']) == 0:
                logger.error(f"Nie znaleziono filmu dla ID: {video_id}")
                return None
            
            video = response['items'][0]
            video_data = {
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
                'thumbnail': video['snippet']['thumbnails']['default']['url'],
                'url': f"https://www.youtube.com/watch?v={video['id']}"
            }
            
            # Zapisz do cache
            self.video_cache[video_id] = {
                'data': video_data,
                'timestamp': datetime.now().timestamp()
            }
            self.save_cache()
            
            logger.debug(f"Pobrano z API i zapisano do cache: {video_id}")
            return video_data
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szczegółów filmu {video_id}: {e}")
            return None

    async def _get_video_details_batch(self, video_ids: List[str]) -> List[Dict]:
        """Pobiera szczegóły wielu filmów za jednym razem (batch processing)"""
        if not video_ids:
            return []
        
        # Sprawdź cache dla wszystkich filmów
        cached_videos = []
        uncached_ids = []
        
        for video_id in video_ids:
            if video_id in self.video_cache:
                cache_data = self.video_cache[video_id]
                cache_age = datetime.now().timestamp() - cache_data['timestamp']
                
                # Cache ważny przez 24h
                if cache_age < 86400:
                    cached_videos.append(cache_data['data'])
                    logger.debug(f"Pobrano z cache (batch): {video_id}")
                else:
                    # Usuń przestarzały cache
                    del self.video_cache[video_id]
                    uncached_ids.append(video_id)
            else:
                uncached_ids.append(video_id)
        
        # Pobierz z API filmy, których nie ma w cache
        if uncached_ids:
            logger.info(f"Pobieranie {len(uncached_ids)} filmów z API (batch)")
            
            # YouTube API pozwala na max 50 ID w jednym zapytaniu
            batch_size = 50
            all_videos = []
            
            for i in range(0, len(uncached_ids), batch_size):
                batch_ids = uncached_ids[i:i+batch_size]
                
                try:
                    request = self.service.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=','.join(batch_ids)
                    )
                    response = request.execute()
                    if self.state_manager:
                        self.state_manager.add_quota_used(1)  # Tylko 1 quota za 50 filmów!
                    
                    if 'items' in response:
                        for video in response['items']:
                            video_data = {
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
                                'thumbnail': video['snippet']['thumbnails']['default']['url'],
                                'url': f"https://www.youtube.com/watch?v={video['id']}"
                            }
                            
                            # Zapisz do cache
                            self.video_cache[video['id']] = {
                                'data': video_data,
                                'timestamp': datetime.now().timestamp()
                            }
                            
                            all_videos.append(video_data)
                    
                    logger.debug(f"Pobrano batch {len(batch_ids)} filmów z API")
                    
                except Exception as e:
                    logger.error(f"Błąd podczas pobierania batch filmów: {e}")
                    # Fallback - pobierz pojedynczo
                    for video_id in batch_ids:
                        try:
                            video_data = await self._get_video_details(video_id)
                            if video_data:
                                all_videos.append(video_data)
                        except Exception as fallback_error:
                            logger.error(f"Błąd fallback dla filmu {video_id}: {fallback_error}")
            
            # Zapisz cache po wszystkich batch requests
            self.save_cache()
            
            # Połącz cached i nowe filmy
            return cached_videos + all_videos
        else:
            logger.info(f"Wszystkie {len(video_ids)} filmów pobrane z cache")
            return cached_videos
    
    def get_quota_usage(self) -> Dict:
        """Zwraca informacje o zużyciu quota"""
        if self.state_manager:
            quota_used = self.state_manager.get_quota_used()
            return {
                'used': quota_used,
                'limit': self.quota_limit,
                'remaining': self.quota_limit - quota_used,
                'percentage': (quota_used / self.quota_limit) * 100
            }
        else:
            return {
                'used': 0,
                'limit': self.quota_limit,
                'remaining': self.quota_limit,
                'percentage': 0
            }
    
    def reset_quota(self):
        """Resetuje licznik quota (wywoływane codziennie)"""
        if self.state_manager:
            self.state_manager.reset_quota()
        logger.info("Quota zostało zresetowane")
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """Czyści przestarzały cache"""
        try:
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            # Znajdź przestarzałe wpisy
            expired_keys = []
            for video_id, cache_data in self.video_cache.items():
                cache_age = current_time - cache_data['timestamp']
                if cache_age > max_age_seconds:
                    expired_keys.append(video_id)
            
            # Usuń przestarzałe wpisy
            for video_id in expired_keys:
                del self.video_cache[video_id]
            
            if expired_keys:
                self.save_cache()
                logger.info(f"Usunięto {len(expired_keys)} przestarzałych wpisów z cache")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """Zwraca statystyki cache"""
        try:
            current_time = datetime.now().timestamp()
            total_entries = len(self.video_cache)
            expired_entries = 0
            
            for cache_data in self.video_cache.values():
                cache_age = current_time - cache_data['timestamp']
                if cache_age > 86400:  # 24h
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'valid_entries': total_entries - expired_entries,
                'cache_size_mb': self.cache_file.stat().st_size / (1024 * 1024) if self.cache_file.exists() else 0
            }
        except Exception as e:
            logger.error(f"Błąd podczas pobierania statystyk cache: {e}")
            return {'error': str(e)} 

    def _is_short_video(self, duration: str) -> bool:
        """Sprawdza czy film jest krótki (shorts)"""
        if not duration:
            return False
        
        # Konwertuj ISO 8601 duration na sekundy
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Filmy do 10 minut (600 sekund) to shorts
            return total_seconds <= 600
        
        return False 