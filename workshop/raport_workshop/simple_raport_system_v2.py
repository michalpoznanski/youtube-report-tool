#!/usr/bin/env python3
"""
UPROSZCZONY SYSTEM RAPORTÓW V2 - Z MONITOROWANIEM QUOTA
======================================================

Cel: Każdy pokój ma swoje kanały, brak mapowania kategorii
NOWE: PEŁNE monitorowanie quota dla wszystkich API calls

AUTOR: Hook Boost V2 - Complete Quota Monitoring
WERSJA: 2.1 (Quota Monitored)
"""

import os
import sys
import json
import glob
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# Dodaj ścieżkę do głównego katalogu
sys.path.append('.')

class SimpleRaportSystemV2:
    """Uproszczony system raportów z PEŁNYM monitorowaniem quota"""
    
    def __init__(self, api_key=None, quota_manager=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("Brak YOUTUBE_API_KEY")
        
        # QUOTA MANAGER - KLUCZOWE!
        self.quota_manager = quota_manager
        if quota_manager:
            print("✅ RaportSystem z monitorowaniem quota")
        else:
            print("⚠️ RaportSystem BEZ monitorowania quota")
        
        # Ustawienia zbierania danych
        self.days_back = 7  # Zawsze 7 dni
        self.max_results_per_channel = 50  # Do sprawdzenia dat
        
        # Załaduj konfigurację kanałów
        self.channels_config = {}
        self._load_channels_config()
        
        # Statystyki sesji
        self.session_quota_used = 0
        self.session_videos_collected = 0
        self.session_channels_processed = 0
        
    def _load_channels_config(self):
        """Ładuje konfigurację kanałów"""
        try:
            with open('channels_config.json', 'r', encoding='utf-8') as f:
                self.channels_config = json.load(f)
        except FileNotFoundError:
            self.channels_config = {'channels': {}}
        except Exception as e:
            print(f"❌ Błąd ładowania channels_config.json: {e}")
            self.channels_config = {'channels': {}}
    
    def _api_call_with_monitoring(self, operation_type, url, params, description=""):
        """Wykonuje API call z MONITOROWANIEM QUOTA"""
        
        # Szacuj koszt
        if operation_type == 'playlistItems':
            estimated_cost = 1
        elif operation_type == 'channels':
            estimated_cost = 1
        elif operation_type == 'search':
            estimated_cost = 100
        else:
            estimated_cost = 1
        
        try:
            print(f"🔄 API call: {operation_type} ({estimated_cost} quota) - {description}")
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # LOGUJ SUKCES
            if self.quota_manager:
                self.quota_manager.log_operation(
                    operation_type,
                    {'description': description, 'url': url},
                    estimated_cost,
                    True  # success
                )
            
            self.session_quota_used += estimated_cost
            print(f"✅ API call sukces: +{estimated_cost} quota (sesja: {self.session_quota_used})")
            
            return data
            
        except Exception as e:
            print(f"❌ API call błąd: {operation_type} - {e}")
            
            # LOGUJ BŁĄD - quota było wydane mimo błędu
            if self.quota_manager:
                self.quota_manager.log_operation(
                    operation_type,
                    {'description': description, 'error': str(e)},
                    estimated_cost,
                    False  # success = False
                )
            
            self.session_quota_used += estimated_cost
            raise
    
    def get_channel_uploads_playlist(self, channel_id):
        """Pobiera playlist ID kanału z MONITOROWANIEM"""
        
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'contentDetails',
            'id': channel_id,
            'key': self.api_key
        }
        
        data = self._api_call_with_monitoring(
            'channels',
            url,
            params,
            f"Get uploads playlist for {channel_id[:8]}..."
        )
        
        if data.get('items'):
            return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        return None
    
    def get_recent_videos_from_playlist(self, playlist_id, channel_id):
        """Pobiera najnowsze filmy z playlisty z MONITOROWANIEM"""
        
        # Data graniczna (7 dni wstecz)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        
        videos = []
        next_page_token = None
        
        while len(videos) < 200:  # Bezpiecznik
            url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': 50,
                'key': self.api_key
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            data = self._api_call_with_monitoring(
                'playlistItems',
                url,
                params,
                f"Get videos from {channel_id[:8]}... (page {len(videos)//50 + 1})"
            )
            
            if not data.get('items'):
                break
            
            # Filtruj filmy według daty
            page_videos = []
            for item in data['items']:
                try:
                    published_str = item['snippet']['publishedAt']
                    published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    
                    if published_date >= cutoff_date:
                        page_videos.append({
                            'video_id': item['snippet']['resourceId']['videoId'],
                            'title': item['snippet']['title'],
                            'published_at': published_str,
                            'channel_id': channel_id
                        })
                    else:
                        # Filmy starsze niż 7 dni - przerwij
                        print(f"📅 Znaleziono filmy starsze niż {self.days_back} dni - przerywam")
                        videos.extend(page_videos)
                        return videos
                        
                except Exception as e:
                    print(f"⚠️ Błąd parsowania filmu: {e}")
                    continue
            
            videos.extend(page_videos)
            
            # Sprawdź czy jest następna strona
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
            
            # Bezpieczne opóźnienie
            time.sleep(0.1)
        
        print(f"📊 Kanał {channel_id[:8]}...: {len(videos)} filmów z ostatnich {self.days_back} dni")
        return videos
    
    def collect_room_data(self, room_name, channel_ids=None):
        """
        Zbiera dane dla konkretnego pokoju z MONITOROWANIEM QUOTA
        
        Args:
            room_name: Nazwa pokoju Discord
            channel_ids: Lista Channel ID (opcjonalne, domyślnie z config)
        
        Returns:
            Dict z wynikami i statystykami quota
        """
        
        # Reset statystyk sesji
        self.session_quota_used = 0
        self.session_videos_collected = 0
        self.session_channels_processed = 0
        
        print(f"🎯 Rozpoczynam zbieranie danych dla pokoju: {room_name}")
        print(f"⛽ MONITOROWANIE QUOTA: {'✅ WŁĄCZONE' if self.quota_manager else '❌ WYŁĄCZONE'}")
        
        # Pobierz kanały do śledzenia
        if not channel_ids:
            channel_ids = self.channels_config.get('channels', {}).get(room_name, [])
        
        if not channel_ids:
            return {
                'success': False,
                'error': f'Brak kanałów do śledzenia w pokoju {room_name}',
                'quota_used': 0
            }
        
        print(f"📺 Kanałów do przetworzenia: {len(channel_ids)}")
        
        all_videos = []
        
        try:
            for i, channel_id in enumerate(channel_ids, 1):
                print(f"\n🔄 Przetwarzam kanał {i}/{len(channel_ids)}: {channel_id[:12]}...")
                
                try:
                    # Pobierz uploads playlist
                    uploads_playlist = self.get_channel_uploads_playlist(channel_id)
                    if not uploads_playlist:
                        print(f"❌ Brak uploads playlist dla {channel_id}")
                        continue
                    
                    # Pobierz najnowsze filmy
                    videos = self.get_recent_videos_from_playlist(uploads_playlist, channel_id)
                    all_videos.extend(videos)
                    
                    self.session_videos_collected += len(videos)
                    self.session_channels_processed += 1
                    
                    print(f"✅ Kanał zakończony: {len(videos)} filmów")
                    
                    # Bezpieczne opóźnienie między kanałami
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"❌ Błąd kanału {channel_id}: {e}")
                    continue
            
            # Zapisz dane do CSV
            if all_videos:
                filename = self._save_to_csv(all_videos, room_name)
                
                print(f"\n🎉 RAPORT ZAKOŃCZONY!")
                print(f"📁 Plik: {filename}")
                print(f"📊 Filmów: {len(all_videos)}")
                print(f"📺 Kanałów: {self.session_channels_processed}/{len(channel_ids)}")
                print(f"⛽ Quota użyte: {self.session_quota_used}")
                
                return {
                    'success': True,
                    'filename': filename,
                    'videos_collected': len(all_videos),
                    'channels_processed': self.session_channels_processed,
                    'quota_used': self.session_quota_used
                }
            else:
                return {
                    'success': False,
                    'error': 'Brak filmów do zapisania',
                    'quota_used': self.session_quota_used
                }
                
        except Exception as e:
            print(f"❌ Błąd krytyczny: {e}")
            return {
                'success': False,
                'error': str(e),
                'quota_used': self.session_quota_used
            }
    
    def _save_to_csv(self, videos, room_name):
        """Zapisuje filmy do pliku CSV"""
        
        import csv
        from datetime import datetime
        
        # Stwórz nazwę pliku
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"reports/youtube_data_{room_name.lower()}_{timestamp}.csv"
        
        # Upewnij się że folder istnieje
        os.makedirs('reports', exist_ok=True)
        
        # Zapisz do CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['video_id', 'title', 'published_at', 'channel_id']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for video in videos:
                writer.writerow(video)
        
        print(f"💾 Zapisano: {filename}")
        return filename 