#!/usr/bin/env python3
"""
SYSTEM RAPORTÓW - WARSZTAT
==========================

ULEPSZONY system do testowania w bezpiecznym środowisku
- Pełne monitorowanie quota
- Tryb demo (test bez prawdziwych API calls)
- Szczegółowe logowanie
- Bezpieczeństwa quota

AUTOR: Hook Boost V2 - Complete Quota Monitoring
WERSJA: Workshop Edition
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

class RaportSystemWorkshop:
    """Ulepszony system raportów - WARSZTAT EDITION"""
    
    def __init__(self, api_key=None, quota_manager=None, demo_mode=False):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key and not demo_mode:
            raise ValueError("Brak YOUTUBE_API_KEY")
        
        # QUOTA MANAGER - KLUCZOWE!
        self.quota_manager = quota_manager
        self.demo_mode = demo_mode
        
        if demo_mode:
            print("🧪 TRYB DEMO - bez prawdziwych API calls")
        elif quota_manager:
            print("✅ RaportSystem z monitorowaniem quota")
        else:
            print("⚠️ RaportSystem BEZ monitorowania quota")
        
        # Ustawienia zbierania danych - CODZIENNE!
        self.days_back = 1  # ZMIANA: 1 dzień zamiast 7
        self.max_results_per_channel = 20  # Mniej filmów bo 24h
        
        # Załaduj konfigurację kanałów
        self.channels_config = {}
        self._load_channels_config()
        
        # Statystyki sesji
        self.session_quota_used = 0
        self.session_videos_collected = 0
        self.session_channels_processed = 0
        
        # Demo data dla testów
        self.demo_channels = {
            'polityka': [
                'UC_TVP_Info_Channel_ID',
                'UC_PolsatNews_Channel_ID', 
                'UC_TVN24_Channel_ID'
            ],
            'showbiz': [
                'UC_Pudelek_Channel_ID',
                'UC_PartyTV_Channel_ID'
            ],
            'motoryzacja': [
                'UC_Moto_Channel_ID'
            ]
        }
        
    def _load_channels_config(self):
        """Ładuje konfigurację kanałów"""
        try:
            config_path = 'channels_config.json'
            print(f"🔍 Szukam konfiguracji: {os.path.abspath(config_path)}")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.channels_config = json.load(f)
                print(f"✅ Załadowano konfigurację: {len(self.channels_config.get('channels', {}))} pokojów")
                print(f"📊 Kanały w showbiz: {len(self.channels_config.get('channels', {}).get('showbiz', []))}")
            else:
                print("⚠️ Brak channels_config.json - używam pustej konfiguracji")
                self.channels_config = {'channels': {}}
        except Exception as e:
            print(f"❌ Błąd ładowania konfiguracji: {e}")
            self.channels_config = {'channels': {}}
    
    def get_channels_for_room(self, room_name: str) -> List[str]:
        """Pobiera kanały dla konkretnego pokoju Discord"""
        if self.demo_mode:
            return self.demo_channels.get(room_name.lower(), [])
        
        channels = self.channels_config.get('channels', {}).get(room_name, [])
        print(f"🔍 get_channels_for_room('{room_name}'): {len(channels)} kanałów")
        print(f"📊 Konfiguracja: {self.channels_config.get('channels', {}).keys()}")
        return channels

    def demo_collect_data(self, room_name: str) -> Dict:
        """Demo zbierania danych - symulacja bez API calls"""
        print(f"🧪 DEMO: Symulacja zbierania danych dla pokoju '{room_name}'")
        
        channels = self.get_channels_for_room(room_name)
        
        if not channels:
            return {
                'success': False,
                'error': f'Brak kanałów dla pokoju: {room_name}',
                'demo': True
            }
        
        # Symuluj zbieranie danych
        simulated_videos = []
        simulated_quota = 0
        
        for i, channel_id in enumerate(channels, 1):
            print(f"🔄 DEMO - Kanał {i}/{len(channels)}: {channel_id}")
            
            # Symuluj API calls
            channel_quota = 1  # channels().list()
            playlist_quota = 1  # playlistItems().list()
            videos_per_channel = 5 + (i * 3)  # Symulowane filmy
            
            simulated_quota += channel_quota + playlist_quota
            simulated_videos.extend([f"demo_video_{channel_id}_{j}" for j in range(videos_per_channel)])
            
            print(f"  📊 Symulowane: {videos_per_channel} filmów, {channel_quota + playlist_quota} quota")
            time.sleep(0.1)  # Symulacja opóźnienia
        
        # Zapisz demo raport
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        demo_filename = f"workshop/demo_report_{room_name.lower()}_{timestamp}.json"
        
        demo_data = {
            'room_name': room_name,
            'channels_processed': len(channels),
            'videos_collected': len(simulated_videos),
            'quota_used': simulated_quota,
            'demo': True,
            'timestamp': timestamp,
            'sample_videos': simulated_videos[:10]  # Pierwsze 10
        }
        
        os.makedirs('workshop', exist_ok=True)
        with open(demo_filename, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 DEMO ZAKOŃCZONE!")
        print(f"📁 Demo plik: {demo_filename}")
        print(f"📊 Symulowane filmy: {len(simulated_videos)}")
        print(f"📺 Kanałów: {len(channels)}")
        print(f"⛽ Symulowane quota: {simulated_quota}")
        
        return {
            'success': True,
            'demo': True,
            'filename': demo_filename,
            'videos_collected': len(simulated_videos),
            'channels_processed': len(channels),
            'quota_used': simulated_quota
        }

    def save_daily_raw_data(self, room_name: str, videos_data: List[Dict]) -> str:
        """Zapisuje surowe dane do folderu raw_data w formacie JSON i robi backup do reports/backup/"""
        
        # Utwórz folder raw_data - POPRAWKA DLA RAILWAY
        raw_data_dir = "raw_data"  # ZMIANA: bez ../
        os.makedirs(raw_data_dir, exist_ok=True)
        
        # Przygotuj dane do zapisu
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().isoformat()
        
        raw_data = {
            'room': room_name,
            'date': today,
            'generated_at': timestamp,
            'videos': videos_data,
            'channels_processed': self.session_channels_processed,
            'total_videos': len(videos_data),
            'quota_used': self.session_quota_used,
            'days_back': self.days_back,
            'demo': self.demo_mode
        }
        
        # Nazwa pliku: raw_raport_YYYY-MM-DD_room.json
        filename = f"raw_raport_{today}_{room_name}.json"
        filepath = os.path.join(raw_data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Raw data zapisane: {filepath}")
            
            # AUTOMATYCZNY BACKUP - zapisz również CSV i JSON do reports/backup/
            self._save_csv_backup(room_name, videos_data, raw_data)
            self._backup_to_reports_backup(filepath, videos_data, raw_data)
            
            return filepath
                        
        except Exception as e:
            print(f"❌ Błąd zapisu raw data: {e}")
            return ""

    def _backup_to_reports_backup(self, json_path, videos_data, raw_data):
        """Kopiuje plik JSON i generuje CSV do katalogu reports/backup/ + auto-commit do GitHub"""
        import shutil
        import subprocess
        
        backup_dir = os.path.join(os.path.dirname(__file__), '../../reports/backup')
        backup_dir = os.path.abspath(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Kopiuj JSON
        try:
            shutil.copy(json_path, backup_dir)
            print(f"✅ Backup JSON do {backup_dir}")
        except Exception as e:
            print(f"❌ Błąd backupu JSON: {e}")
            
        # Zapisz CSV
        try:
            import csv
            today = raw_data.get('date', 'unknown')
            room = raw_data.get('room', 'unknown')
            csv_name = f"raw_raport_{today}_{room}.csv"
            csv_path = os.path.join(backup_dir, csv_name)
            if videos_data:
                with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=videos_data[0].keys())
                    writer.writeheader()
                    writer.writerows(videos_data)
                print(f"✅ Backup CSV do {csv_path}")
            else:
                print("⚠️ Brak danych do backupu CSV")
        except Exception as e:
            print(f"❌ Błąd backupu CSV: {e}")
        
        # AUTO-COMMIT DO GITHUB
        self._auto_commit_to_github(json_path, csv_path if 'csv_path' in locals() else None, raw_data)
    
    def _auto_commit_to_github(self, json_path, csv_path, raw_data):
        """Automatyczny commit raportów do GitHub"""
        try:
            import os
            import subprocess
            from datetime import datetime
            
            # Sprawdź czy jesteśmy w git repo
            result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='.')
            if result.returncode != 0:
                print("⚠️ Nie jesteśmy w git repository - pomijam auto-commit")
                return
            
            # Dodaj pliki do git
            files_to_commit = []
            
            if os.path.exists(json_path):
                subprocess.run(['git', 'add', json_path], cwd='.')
                files_to_commit.append("JSON")
            
            if csv_path and os.path.exists(csv_path):
                subprocess.run(['git', 'add', csv_path], cwd='.')
                files_to_commit.append("CSV")
            
            if not files_to_commit:
                print("⚠️ Brak plików do commit")
                return
            
            # Commit message
            room = raw_data.get('room', 'unknown')
            date = raw_data.get('date', 'unknown')
            videos_count = raw_data.get('total_videos', 0)
            quota_used = raw_data.get('quota_used', 0)
            
            commit_msg = f"🤖 Auto-raport {room} {date}: {videos_count} filmów, {quota_used} quota [{', '.join(files_to_commit)}]"
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print(f"✅ Git commit: {commit_msg}")
                
                # Push do GitHub
                push_result = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd='.')
                if push_result.returncode == 0:
                    print(f"✅ Git push successful - raport dostępny na GitHub!")
                else:
                    print(f"❌ Git push failed: {push_result.stderr}")
            else:
                print(f"❌ Git commit failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Błąd auto-commit: {e}")
    
    def test_room_configuration(self) -> Dict:
        """Testuje konfigurację pokojów"""
        print("🧪 TEST KONFIGURACJI POKOJÓW")
        print("=" * 40)
        
        test_results = {}
        
        test_rooms = ['polityka', 'showbiz', 'motoryzacja', 'podcast', 'nieznany']
        
        for room in test_rooms:
            channels = self.get_channels_for_room(room)
            test_results[room] = {
                'channels_count': len(channels),
                'channels': channels,
                'has_channels': len(channels) > 0
            }
            
            status = "✅" if len(channels) > 0 else "❌"
            print(f"{status} {room}: {len(channels)} kanałów")
            
            if channels and self.demo_mode:
                for i, ch in enumerate(channels[:3], 1):
                    print(f"    {i}. {ch}")
                if len(channels) > 3:
                    print(f"    ... i {len(channels) - 3} więcej")
        
        return test_results 

    def collect_room_data(self, room_name, channel_ids=None):
        """
        Zbiera dane dla konkretnego pokoju z MONITOROWANIEM QUOTA
        Kompatybilna metoda dla Hook Boost Discord bot
        
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
        print(f"🔍 Przekazane channel_ids: {channel_ids}")
        
        # Pobierz kanały do śledzenia
        if not channel_ids:
            print("⚠️ Brak przekazanych channel_ids - pobieram z config")
            channel_ids = self.get_channels_for_room(room_name)
        else:
            print(f"✅ Używam przekazanych channel_ids: {len(channel_ids)} kanałów")
        
        if not channel_ids:
            print("❌ BRAK KANAŁÓW DO ŚLEDZENIA!")
            return {
                'success': False,
                'error': f'Brak kanałów do śledzenia w pokoju {room_name}',
                'quota_used': 0
            }
        
        print(f"📺 Kanałów do przetworzenia: {len(channel_ids)}")
        print(f"📋 Lista kanałów: {channel_ids[:3]}...")  # Pierwsze 3
        
        try:
            # W trybie demo
            if self.demo_mode:
                result = self.demo_collect_data(room_name)
                
                # Zapisz raw data (nawet demo)
                raw_file = self.save_daily_raw_data(room_name, result.get('videos', []))
                
                return {
                    'success': True,
                    'filename': raw_file or f"demo_raport_{room_name}.json",
                    'channels_processed': result.get('channels_processed', len(channel_ids)),
                    'videos_collected': result.get('videos_collected', 0),
                    'quota_used': result.get('quota_used', 0)
                }
            
            # PRAWDZIWE ZBIERANIE DANYCH
            all_videos = []
            
            for i, channel_id in enumerate(channel_ids, 1):
                print(f"\n🔄 Przetwarzam kanał {i}/{len(channel_ids)}: {channel_id[:12]}...")
                
                try:
                    # Pobierz uploads playlist
                    uploads_playlist = self._get_channel_uploads_playlist(channel_id)
                    if not uploads_playlist:
                        print(f"❌ Brak uploads playlist dla {channel_id}")
                        continue
                    
                    # Pobierz najnowsze filmy (ostatnie 24h)
                    videos = self._get_recent_videos_from_playlist(uploads_playlist, channel_id)
                    all_videos.extend(videos)
                    
                    self.session_videos_collected += len(videos)
                    self.session_channels_processed += 1
                    
                    print(f"✅ Kanał zakończony: {len(videos)} filmów")
                    
                    # Bezpieczne opóźnienie między kanałami
                    import time
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"❌ Błąd kanału {channel_id}: {e}")
                    continue
            
            # Zapisz raw data jako JSON
            raw_file = self.save_daily_raw_data(room_name, all_videos)
            
            print(f"\n🎉 PRAWDZIWY RAPORT ZAKOŃCZONY!")
            print(f"📁 Plik: {raw_file}")
            print(f"📊 Filmów: {len(all_videos)}")
            print(f"📺 Kanałów: {self.session_channels_processed}/{len(channel_ids)}")
            print(f"⛽ Quota użyte: {self.session_quota_used}")
            
            return {
                'success': True,
                'filename': raw_file or f"raport_{room_name}.json",
                'videos_collected': len(all_videos),
                'channels_processed': self.session_channels_processed,
                'quota_used': self.session_quota_used
            }
            
        except Exception as e:
            print(f"❌ BŁĄD collect_room_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'quota_used': self.session_quota_used
            }

    def _get_channel_uploads_playlist(self, channel_id):
        """Pobiera ID uploads playlist dla kanału"""
        if not self.api_key:
            print("❌ Brak API key")
            return None
        
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'contentDetails',
            'id': channel_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Loguj quota (1 quota za channels call)
            if self.quota_manager:
                self.quota_manager.log_operation('channels', {'channel_id': channel_id}, 1, True)
                self.session_quota_used += 1
            
            if data.get('items'):
                return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            return None
            
        except Exception as e:
            print(f"❌ Błąd pobierania playlist: {e}")
            if self.quota_manager:
                self.quota_manager.log_operation('channels', {'channel_id': channel_id}, 1, False)
            return None
    
    def _get_recent_videos_from_playlist(self, playlist_id, channel_id):
        """Pobiera najnowsze filmy z ostatnich 24h"""
        if not self.api_key:
            print("❌ Brak API key")
            return []
        
        from datetime import datetime, timezone, timedelta
        
        # Data graniczna (24h wstecz)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        
        videos = []
        next_page_token = None
        
        while len(videos) < self.max_results_per_channel:
            url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': min(50, self.max_results_per_channel - len(videos)),
                'key': self.api_key
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                # Loguj quota (1 quota za playlistItems call)
                if self.quota_manager:
                    self.quota_manager.log_operation('playlistItems', {'playlist_id': playlist_id, 'channel_id': channel_id}, 1, True)
                    self.session_quota_used += 1
                
                if not data.get('items'):
                    break
                
                page_videos = []
                for item in data['items']:
                    try:
                        # Sprawdź datę publikacji
                        publish_date_str = item['snippet']['publishedAt']
                        publish_date = datetime.fromisoformat(publish_date_str.replace('Z', '+00:00'))
                        
                        # Tylko filmy z ostatnich 24h
                        if publish_date >= cutoff_date:
                            video_data = {
                                'Channel_ID': channel_id,
                                'Video_ID': item['snippet']['resourceId']['videoId'],
                                'Title': item['snippet']['title'],
                                'Published_Date': publish_date_str,
                                'Channel_Title': item['snippet']['channelTitle'],
                                'Thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', ''),
                                'Description': item['snippet'].get('description', '')[:200],  # Pierwsze 200 znaków
                                'Position': item['snippet']['position']
                            }
                            page_videos.append(video_data)
                        else:
                            # Jeśli natrafimy na starszy film, przerywamy
                            break
                    
                    except Exception as e:
                        print(f"⚠️ Błąd przetwarzania filmu: {e}")
                        continue
                
                videos.extend(page_videos)
                
                # Jeśli nie ma więcej stron lub natrafimy na stare filmy
                next_page_token = data.get('nextPageToken')
                if not next_page_token or len(page_videos) == 0:
                    break
                
            except Exception as e:
                print(f"❌ Błąd pobierania filmów: {e}")
                if self.quota_manager:
                    self.quota_manager.log_operation('playlistItems', {'playlist_id': playlist_id, 'channel_id': channel_id}, 1, False)
                break
        
        print(f"📊 Kanał {channel_id[:8]}...: {len(videos)} filmów z ostatnich {self.days_back} dni")
        return videos

# PRODUKCYJNY SYSTEM RAPORTÓW
if __name__ == "__main__":
    print("🎯 SYSTEM RAPORTÓW - PRODUKCJA")
    print("=" * 50)
    
    try:
        demo_system = RaportSystemWorkshop(demo_mode=True)
        config_results = demo_system.test_room_configuration()
        
        print(f"\n✅ SYSTEM GOTOWY DO PRODUKCJI")
        
    except Exception as e:
        print(f"❌ BŁĄD SYSTEMU: {e}")
        import traceback
        traceback.print_exc() 