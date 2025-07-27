#!/usr/bin/env python3
"""
SMART DATE COLLECTOR - Inteligentne pobieranie TYLKO filmów z określonego okresu
GŁÓWNY CEL: Oszczędność quota przez filtrowanie po datach

NOWA LOGIKA:
1. Pobierz tylko filmy z ostatnich X dni
2. Używaj publishedAfter parameter w API
3. Zmniejsz maxResults do minimum
4. Batch processing dla efektywności
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from quota_manager import QuotaManager


class SmartDateCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.quota_manager = QuotaManager(api_key)
        
        # USTAWIENIA PRODUKCYJNE
        self.DEFAULT_DAYS = 7  # 7 dni jak w głównym bocie
        self.MAX_RESULTS_PER_CHANNEL = 50  # 50 filmów na kanał
        self.BATCH_SIZE = 50
        
    def calculate_date_range(self, days_back: int) -> tuple:
        """Oblicza zakres dat dla filtrowania"""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days_back)
        
        # Format ISO 8601 dla YouTube API
        published_after = start_date.isoformat()
        published_before = now.isoformat()
        
        return published_after, published_before
    
    def estimate_smart_cost(self, channels: list, days: int) -> dict:
        """Szacuje koszt z uwzględnieniem filtrowania dat"""
        
        # Na podstawie analizy: średnio 1.5 filmu na dzień na kanał
        estimated_videos_per_day = 1.5
        estimated_total_videos = len(channels) * days * estimated_videos_per_day
        
        # Koszty
        costs = {
            'channel_resolution': 0,
            'video_search': 0, 
            'video_details': 0,
            'total': 0
        }
        
        # Handles vs Channel IDs
        channel_ids = [ch for ch in channels if ch.startswith('UC') and len(ch) == 24]
        handles = [ch for ch in channels if not (ch.startswith('UC') and len(ch) == 24)]
        
        # 1. Rozwiązywanie handles (jeśli są)
        if handles:
            costs['channel_resolution'] = len(handles) * 1
        
        # 2. Search za pomocą search().list() LUB playlistItems().list()
        # playlistItems().list() = 1 quota (lepsze niż search = 100 quota!)
        # Ale wymaga uploads playlist ID
        costs['video_search'] = len(channels) * 1  # Optimistic: użyjemy playlistItems
        
        # 3. Video details
        costs['video_details'] = max(1, int(estimated_total_videos) // 50)
        
        costs['total'] = sum(costs.values())
        
        return {
            'costs': costs,
            'estimated_videos': int(estimated_total_videos),
            'days': days,
            'channels': len(channels),
            'videos_per_channel_per_day': estimated_videos_per_day,
            'optimization': 'playlistItems + date filtering'
        }
    
    def can_collect_safely(self, channels: list, days: int = 1) -> dict:
        """Sprawdza czy można bezpiecznie zebrać dane"""
        
        # Sprawdź quota
        quota_summary = self.quota_manager.get_quota_summary()
        remaining_quota = quota_summary['today_remaining']
        
        # Szacuj koszt
        cost_estimate = self.estimate_smart_cost(channels, days)
        
        # Sprawdź limity
        checks = {
            'quota_available': remaining_quota > 0,
            'quota_sufficient': remaining_quota >= cost_estimate['costs']['total'],
            'channels_within_limit': len(channels) <= 10,  # Limit produkcji
            'cost_acceptable': cost_estimate['costs']['total'] < 1000  # Limit produkcji
        }
        
        all_safe = all(checks.values())
        
        return {
            'safe': all_safe,
            'checks': checks,
            'remaining_quota': remaining_quota,
            'estimated_cost': cost_estimate['costs']['total'],
            'cost_breakdown': cost_estimate
        }
    
    def get_channel_uploads_playlist(self, channel_identifier: str) -> str:
        """Pobiera uploads playlist ID dla kanału"""
        try:
            # Sprawdź czy to Channel ID czy handle
            if channel_identifier.startswith('UC') and len(channel_identifier) == 24:
                # Channel ID
                request = self.youtube.channels().list(
                    part='contentDetails',
                    id=channel_identifier
                )
            else:
                # Handle - trzeba najpierw rozwiązać do Channel ID
                search_request = self.youtube.channels().list(
                    part='contentDetails',
                    forUsername=channel_identifier  # Dla starych usernames
                )
                # Jeśli nie działa, próbuj search
                response = search_request.execute()
                if not response['items']:
                    # Fallback: search by handle
                    search_fallback = self.youtube.search().list(
                        part='snippet',
                        q=f'@{channel_identifier}',
                        type='channel',
                        maxResults=1
                    )
                    search_response = search_fallback.execute()
                    if search_response['items']:
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        request = self.youtube.channels().list(
                            part='contentDetails',
                            id=channel_id
                        )
                    else:
                        return None
                else:
                    request = search_request
            
            response = request.execute()
            
            if response['items']:
                uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                return uploads_id
            
            return None
            
        except Exception as e:
            print(f"⚠️ Błąd pobierania uploads playlist dla {channel_identifier}: {e}")
            return None
    
    def collect_videos_smart(self, channels: list, days: int = 7, dry_run: bool = True) -> dict:
        """INTELIGENTNE zbieranie filmów z filtrową według dat"""
        
        # Sprawdź bezpieczeństwo
        cost_estimate = self.estimate_smart_cost(channels, days)
        
        if cost_estimate['costs']['total'] > 1000:
            return {
                'success': False,
                'error': f"Koszt {cost_estimate['costs']['total']} quota przekracza bezpieczny limit",
                'cost_estimate': cost_estimate
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'cost_estimate': cost_estimate,
                'message': f"DRY RUN: Zebrałbym ~{cost_estimate['estimated_videos']} filmów z {len(channels)} kanałów ({days} dni)",
                'optimization_used': cost_estimate['optimization']
            }
        
        print(f"🚀 RZECZYWISTE POBIERANIE: {len(channels)} kanałów, {days} dni")
        print(f"💰 Szacowany koszt: {cost_estimate['costs']['total']} quota")
        
        # Oblicz zakres dat
        published_after, published_before = self.calculate_date_range(days)
        
        all_videos_data = []
        processed_channels = 0
        
        # Wszystkie kanały
        all_channels = channels
        
        for channel in all_channels:
            try:
                print(f"📺 Przetwarzam kanał: {channel}")
                
                # Pobierz uploads playlist ID
                uploads_playlist = self.get_channel_uploads_playlist(channel)
                
                if not uploads_playlist:
                    print(f"⚠️ Nie można znaleźć uploads playlist dla {channel}")
                    continue
                
                # Pobierz filmy z uploads playlist
                playlist_request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist,
                    maxResults=self.MAX_RESULTS_PER_CHANNEL
                )
                
                playlist_response = playlist_request.execute()
                print(f"📋 Znaleziono {len(playlist_response['items'])} filmów")
                
                # Filtruj po dacie
                recent_videos = []
                start_date = datetime.fromisoformat(published_after.replace('Z', '+00:00'))
                
                for item in playlist_response['items']:
                    video_date = datetime.fromisoformat(
                        item['snippet']['publishedAt'].replace('Z', '+00:00')
                    )
                    
                    if video_date >= start_date:
                        recent_videos.append(item['snippet']['resourceId']['videoId'])
                
                print(f"📅 {len(recent_videos)} filmów z ostatnich {days} dni")
                
                if recent_videos:
                    # Pobierz szczegóły filmów
                    videos_request = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=','.join(recent_videos)
                    )
                    
                    videos_response = videos_request.execute()
                    
                    # Przetworz każdy film na format CSV
                    for video in videos_response['items']:
                        video_data = self._process_video_to_csv_format(video)
                        all_videos_data.append(video_data)
                    
                    print(f"✅ Przetworzone: {len(videos_response['items'])} filmów")
                
                processed_channels += 1
                
            except Exception as e:
                print(f"❌ Błąd kanału {channel}: {e}")
                continue
        
        # Utwórz DataFrame i zapisz CSV
        if all_videos_data:
            df = pd.DataFrame(all_videos_data)
            
            # Nazwa pliku
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            csv_filename = f'test_data_smart_collector_{timestamp}.csv'
            
            # Zapisz CSV
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"💾 Zapisano: {csv_filename}")
            
            return {
                'success': True,
                'videos_collected': len(all_videos_data),
                'channels_processed': processed_channels,
                'csv_file': csv_filename,
                'date_range': f"{published_after[:10]} - {published_before[:10]}",
                'cost_estimate': cost_estimate
            }
        else:
            return {
                'success': False,
                'error': 'Brak danych do zapisania',
                'channels_processed': processed_channels
            }
    
    def _process_video_to_csv_format(self, video: dict) -> dict:
        """Przetwarza video na format CSV kompatybilny z obecnym systemem"""
        snippet = video['snippet']
        stats = video.get('statistics', {})
        content_details = video.get('contentDetails', {})
        
        # Konwertuj datę
        published_at = snippet['publishedAt']
        try:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            gmt2_time = dt.astimezone(timezone(timedelta(hours=2)))
            date_str = gmt2_time.strftime('%Y-%m-%d')
            hour_str = gmt2_time.strftime('%H:%M')
        except:
            date_str = published_at[:10]
            hour_str = '00:00'
        
        # Określ typ filmu
        duration = content_details.get('duration', '')
        if 'PT' in duration and 'M' not in duration and 'H' not in duration:
            # Krótkie video (tylko sekundy)
            video_type = 'shorts'
        elif 'PT' in duration and 'M' in duration and 'H' not in duration:
            # Sprawdź czy to krótkie video (mniej niż 1 minuta)
            import re
            minutes_match = re.search(r'(\d+)M', duration)
            if minutes_match and int(minutes_match.group(1)) <= 1:
                video_type = 'shorts'
            else:
                video_type = 'video'
        else:
            video_type = 'video'
        
        return {
            'Channel_Name': snippet['channelTitle'],
            'Date_of_Publishing': date_str,
            'Hour_GMT2': hour_str,
            'Title': snippet['title'],
            'Description': snippet.get('description', ''),
            'Tags': ';'.join(snippet.get('tags', [])),
            'Video_Type': video_type,
            'View_Count': int(stats.get('viewCount', 0)),
            'Like_Count': int(stats.get('likeCount', 0)),
            'Comment_Count': int(stats.get('commentCount', 0)),
            'Favorite_Count': int(stats.get('favoriteCount', 0)),
            'Definition': content_details.get('definition', 'sd'),
            'Has_Captions': content_details.get('caption', 'false'),
            'Licensed_Content': str(content_details.get('licensedContent', False)),
            'Video_ID': video['id']
        }
    



# TESTY OPTYMALIZACJI
if __name__ == "__main__":
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Brak YOUTUBE_API_KEY")
        exit(1)
    
    collector = SmartDateCollector(api_key)
    
    print("🧠 SMART DATE COLLECTOR - OPTYMALIZACJA")
    print("=" * 45)
    
    # Test kanały
    test_channels = [
        "UC-wh71MEZ4KAx94aZyoG_qg",
        "UCvHFbkohgX29NhaUtmkzLmg", 
        "radiozet"
    ]
    
    # Porównanie kosztów
    print("💰 PORÓWNANIE KOSZTÓW:")
    
    scenarios = [
        (3, "3 dni (zalecane)"),
        (7, "7 dni (obecne)"),
        (1, "1 dzień (oszczędne)")
    ]
    
    for days, desc in scenarios:
        cost = collector.estimate_smart_cost(test_channels, days)
        print(f"  {desc}: {cost['costs']['total']} quota (~{cost['estimated_videos']} filmów)")
    
    # Test dla 50 kanałów
    print(f"\n🎯 SYMULACJA: 50 KANAŁÓW")
    big_channels = ["test"] * 50
    
    for days, desc in scenarios:
        cost = collector.estimate_smart_cost(big_channels, days)
        percentage = (cost['costs']['total'] / 10000) * 100
        print(f"  {desc}: {cost['costs']['total']:,} quota ({percentage:.1f}% dziennego limitu)")
    
    # Dry run test
    print(f"\n🧪 DRY RUN TEST:")
    result = collector.collect_videos_smart(test_channels, 3, dry_run=True)
    print(f"  {result.get('message', 'ERROR')}")
    print(f"  Optymalizacja: {result.get('optimization_used', 'N/A')}") 