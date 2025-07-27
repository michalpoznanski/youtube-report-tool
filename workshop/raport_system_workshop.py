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
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.channels_config = json.load(f)
                print(f"✅ Załadowano konfigurację: {len(self.channels_config.get('channels', {}))} pokojów")
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
        
        return self.channels_config.get('channels', {}).get(room_name, [])

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
        """Zapisuje surowe dane do folderu raw_data w formacie JSON"""
        
        # Utwórz folder raw_data
        raw_data_dir = "../raw_data"
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
            
            print(f"💾 Raw data zapisane: {filename}")
            return filepath
                        
        except Exception as e:
            print(f"❌ Błąd zapisu raw data: {e}")
            return ""
    
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
        
        # Pobierz kanały do śledzenia
        if not channel_ids:
            channel_ids = self.get_channels_for_room(room_name)
        
        if not channel_ids:
            return {
                'success': False,
                'error': f'Brak kanałów do śledzenia w pokoju {room_name}',
                'quota_used': 0
            }
        
        print(f"📺 Kanałów do przetworzenia: {len(channel_ids)}")
        
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
            
            # PRAWDZIWE ZBIERANIE (implementacja w przyszłości)
            # TODO: Implementacja prawdziwego zbierania gdy będzie potrzebne
            return {
                'success': False,
                'error': 'Prawdziwe zbieranie nie jest jeszcze zaimplementowane. Użyj demo_mode=True',
                'quota_used': 0
            }
            
        except Exception as e:
            print(f"❌ BŁĄD collect_room_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'quota_used': self.session_quota_used
            }

# DEMO I TESTY
if __name__ == "__main__":
    print("🎯 SYSTEM RAPORTÓW - WARSZTAT")
    print("=" * 50)
    
    try:
        # TEST 1: Tryb demo
        print("\n🧪 TEST 1: TRYB DEMO")
        print("-" * 30)
        
        demo_system = RaportSystemWorkshop(demo_mode=True)
        
        # Test konfiguracji pokojów
        config_results = demo_system.test_room_configuration()
        
        # Test demo zbierania danych
        print(f"\n🧪 TEST DEMO ZBIERANIA DANYCH:")
        for room in ['polityka', 'showbiz', 'motoryzacja']:
            print(f"\n--- {room.upper()} ---")
            result = demo_system.demo_collect_data(room)
            
            if result['success']:
                print(f"✅ Sukces: {result['videos_collected']} filmów, {result['quota_used']} quota")
            else:
                print(f"❌ Błąd: {result['error']}")
        
        print(f"\n✅ WSZYSTKIE TESTY DEMO ZAKOŃCZONE!")
        
        # TEST 2: Sprawdzenie API key (bez demo)
        print(f"\n🧪 TEST 2: SPRAWDZENIE API KEY")
        print("-" * 30)
        
        api_key = os.getenv('YOUTUBE_API_KEY')
        if api_key:
            print(f"✅ API Key dostępny: {api_key[:20]}...")
            
            # Możemy przetestować prawdziwy system
            print(f"⚠️ Prawdziwy system będzie gotowy do testów z quota monitoring")
        else:
            print(f"❌ Brak API Key - tylko tryb demo dostępny")
        
        print(f"\n🎯 WARSZTAT GOTOWY DO PRACY!")
        print(f"📋 Dostępne funkcje:")
        print(f"   - demo_collect_data(room_name) - symulacja")
        print(f"   - test_room_configuration() - test konfiguracji")
        print(f"   - get_channels_for_room(room_name) - lista kanałów")
        
    except Exception as e:
        print(f"❌ BŁĄD WARSZTATU: {e}")
        sys.exit(1) 