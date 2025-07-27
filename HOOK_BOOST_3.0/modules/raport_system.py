#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAPORT SYSTEM - HOOK BOOST 3.0
===============================

System generowania raportów z 17 kolumnami danych YouTube.
Śledzenie dynamiki wyświetleń przez 3 dni.

AUTOR: Hook Boost 3.0 - Ultra Lean
WERSJA: 3.0 (17-kolumn CSV)
"""

import os
import sys
import json
import csv
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

class RaportSystem:
    """System generowania raportów z 17 kolumnami"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("Brak YOUTUBE_API_KEY")
        
        # QuotaManager usunięty - ultra lean mode
        self.quota_manager = None
        print("⚡ RaportSystem: ultra lean mode (bez quota managera)")
        
        # Ustawienia zbierania danych
        self.days_back = 3  # Śledzenie 3 dni wstecz
        self.max_results_per_channel = 50  # Maksymalnie 50 filmów na kanał
        
        # Koszty quota
        self.CHANNEL_INFO_COST = 1  # Pobranie informacji o kanale
        self.VIDEO_INFO_COST = 1    # Pobranie informacji o filmie
        self.SEARCH_COST = 100      # Wyszukiwanie filmów
        
        print(f"📊 RaportSystem: śledzenie {self.days_back} dni wstecz")
    
    def generate_room_report(self, room_name: str, channel_ids: List[str]) -> Dict:
        """Generuje raport dla pokoju z 17 kolumnami"""
        print(f"📊 Generuję raport dla pokoju: {room_name}")
        print(f"📺 Kanały: {len(channel_ids)}")
        
        # Quota check usunięty - ultra lean mode
        
        # Zbierz dane ze wszystkich kanałów
        all_videos = []
        total_quota_used = 0
        
        for channel_id in channel_ids:
            try:
                print(f"🔍 Przetwarzam kanał: {channel_id}")
                
                # Pobierz informacje o kanale
                channel_info = self._get_channel_info(channel_id)
                if not channel_info:
                    print(f"❌ Nie udało się pobrać informacji o kanale: {channel_id}")
                    continue
                
                # Pobierz filmy z ostatnich 3 dni
                videos = self._get_recent_videos(channel_id, channel_info['name'])
                
                all_videos.extend(videos)
                total_quota_used += len(videos) * self.VIDEO_INFO_COST + self.CHANNEL_INFO_COST
                
                print(f"✅ Kanał {channel_info['name']}: {len(videos)} filmów")
                
            except Exception as e:
                print(f"❌ Błąd przetwarzania kanału {channel_id}: {e}")
        
        if not all_videos:
            return {
                'success': False,
                'error': 'Nie znaleziono żadnych filmów'
            }
        
        # Zapisz raport CSV
        csv_filename = self._save_csv_report(room_name, all_videos)
        
        # Quota logging usunięty - ultra lean mode
        
        return {
            'success': True,
            'channels': len(channel_ids),
            'videos': len(all_videos),
            'filename': csv_filename,
            'quota_used': 0  # Ultra lean mode
        }
    
    def _estimate_quota_cost(self, num_channels: int) -> int:
        """Szacuje koszt quota dla liczby kanałów (ultra lean mode)"""
        # Ultra lean mode - nie szacujemy quota
        return 0
    
    def _get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """Pobiera informacje o kanale"""
        try:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'snippet,statistics',
                'id': channel_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                return {
                    'id': channel_id,
                    'name': item['snippet']['title'],
                    'subscribers': item['statistics'].get('subscriberCount', '0'),
                    'videos': item['statistics'].get('videoCount', '0')
                }
            
        except Exception as e:
            print(f"❌ Błąd pobierania informacji o kanale {channel_id}: {e}")
        
        return None
    
    def _get_recent_videos(self, channel_id: str, channel_name: str) -> List[Dict]:
        """Pobiera filmy z ostatnich 3 dni"""
        videos = []
        
        try:
            # Pobierz playlistę uploads kanału
            uploads_playlist = self._get_uploads_playlist(channel_id)
            if not uploads_playlist:
                return videos
            
            # Pobierz filmy z playlisty
            url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': uploads_playlist,
                'maxResults': self.max_results_per_channel,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Filtruj filmy z ostatnich 3 dni
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
            
            for item in data.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                published_at = datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                
                if published_at >= cutoff_date:
                    # Pobierz szczegółowe informacje o filmie
                    video_info = self._get_video_details(video_id, channel_name, published_at)
                    if video_info:
                        videos.append(video_info)
            
        except Exception as e:
            print(f"❌ Błąd pobierania filmów z kanału {channel_name}: {e}")
        
        return videos
    
    def _get_uploads_playlist(self, channel_id: str) -> Optional[str]:
        """Pobiera ID playlisty uploads kanału"""
        try:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'contentDetails',
                'id': channel_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('items'):
                return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
        except Exception as e:
            print(f"❌ Błąd pobierania playlisty uploads: {e}")
        
        return None
    
    def _get_video_details(self, video_id: str, channel_name: str, published_at: datetime) -> Optional[Dict]:
        """Pobiera szczegółowe informacje o filmie"""
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('items'):
                return None
            
            item = data['items'][0]
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']
            
            # Wyciągnij nazwiska z tytułu i opisu
            names_extracted = self._extract_names(snippet['title'] + ' ' + snippet.get('description', ''))
            
            # Określ typ filmu (shorts vs long)
            video_type = 'shorts' if content_details.get('duration', '') == 'PT0M0S' else 'long'
            
            return {
                'Channel_Name': channel_name,
                'Date_of_Publishing': published_at.strftime('%Y-%m-%d'),
                'Hour_GMT2': published_at.strftime('%H:%M'),
                'Title': snippet['title'],
                'Description': snippet.get('description', '')[:500],  # Ogranicz do 500 znaków
                'Tags': ', '.join(snippet.get('tags', [])),
                'Video_Type': video_type,
                'View_Count': statistics.get('viewCount', '0'),
                'Like_Count': statistics.get('likeCount', '0'),
                'Comment_Count': statistics.get('commentCount', '0'),
                'Favorite_Count': statistics.get('favoriteCount', '0'),
                'Definition': content_details.get('definition', 'sd'),
                'Has_Captions': 'Yes' if content_details.get('caption', 'false') == 'true' else 'No',
                'Licensed_Content': 'Yes' if content_details.get('licensedContent', False) else 'No',
                'Topic_Categories': ', '.join(snippet.get('topicCategories', [])),
                'Names_Extracted': names_extracted,
                'Video_ID': video_id
            }
            
        except Exception as e:
            print(f"❌ Błąd pobierania szczegółów filmu {video_id}: {e}")
        
        return None
    
    def _extract_names(self, text: str) -> str:
        """Wyciąga nazwiska z tekstu (prosta implementacja)"""
        # Prosta implementacja - można rozszerzyć o bardziej zaawansowaną analizę
        import re
        
        # Szukaj wzorców nazwisk (wielka litera + małe litery)
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
        
        # Usuń duplikaty i ogranicz do 5 nazwisk
        unique_names = list(set(names))[:5]
        
        return ', '.join(unique_names)
    
    def _save_csv_report(self, room_name: str, videos: List[Dict]) -> str:
        """Zapisuje raport do pliku CSV"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Utwórz katalog dla dzisiejszej daty
        today_dir = f"data/raw_data/{today}"
        os.makedirs(today_dir, exist_ok=True)
        
        # Nazwa pliku
        filename = f"{room_name}_{today}.csv"
        filepath = os.path.join(today_dir, filename)
        
        # 17 kolumn w kolejności
        columns = [
            'Channel_Name', 'Date_of_Publishing', 'Hour_GMT2', 'Title', 'Description',
            'Tags', 'Video_Type', 'View_Count', 'Like_Count', 'Comment_Count',
            'Favorite_Count', 'Definition', 'Has_Captions', 'Licensed_Content',
            'Topic_Categories', 'Names_Extracted', 'Video_ID'
        ]
        
        # Zapisz CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            writer.writerows(videos)
        
        print(f"✅ Raport zapisany: {filepath}")
        return filename 