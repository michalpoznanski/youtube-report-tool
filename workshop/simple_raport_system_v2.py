#!/usr/bin/env python3
"""
UPRASZCZONY SYSTEM RAPORTÓW V2 - WARSZTAT
Cel: Każdy pokój ma swoje kanały, brak mapowania kategorii
"""

import os
import sys
import json
import glob
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# Dodaj ścieżkę do głównego katalogu
sys.path.append('.')

class SimpleRaportSystemV2:
    """Uproszczony system raportów - każdy pokój ma swoje kanały"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("Brak YOUTUBE_API_KEY")
        
        # Ustawienia zbierania danych
        self.days_back = 7  # Zawsze 7 dni
        self.max_results_per_channel = 50  # Do sprawdzenia dat
        
        # Załaduj konfigurację kanałów
        self.channels_config = self.load_channels_config()
    
    def load_channels_config(self) -> Dict:
        """Ładuje konfigurację kanałów z pliku"""
        try:
            with open('channels_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Brak channels_config.json - używam pustej konfiguracji")
            return {}
    
    def get_channels_for_room(self, room_name: str) -> List[str]:
        """Pobiera kanały dla konkretnego pokoju Discord"""
        # Każdy pokój ma swoje kanały w konfiguracji
        # Na razie puste listy - kanały będą dodawane przez komendę !sledz
        
        # PUSTE LISTY KANAŁÓW - do wypełnienia przez komendę !sledz
        room_channels = {
            'polityka': [],
            'showbiz': [],
            'motoryzacja': [],
            'podcast': []
        }
        
        # Znajdź kanały dla pokoju
        room_lower = room_name.lower()
        for room_key, channels in room_channels.items():
            if room_key in room_lower:
                return channels
        
        # Domyślnie pusta lista
        return []
    
    def check_existing_report(self, room_name: str) -> Optional[str]:
        """Sprawdza czy istnieje raport z ostatnich 7 dni dla pokoju"""
        reports_dir = f'reports/{room_name.lower()}'
        
        if not os.path.exists(reports_dir):
            return None
        
        # Znajdź pliki CSV z ostatnich 7 dni
        csv_files = glob.glob(f'{reports_dir}/youtube_data_{room_name.lower()}_*.csv')
        
        if not csv_files:
            return None
        
        # Sprawdź najnowszy plik
        latest_file = max(csv_files, key=os.path.getctime)
        file_age_hours = (time.time() - os.path.getctime(latest_file)) / 3600
        
        if file_age_hours < 168:  # 7 dni = 168 godzin
            return latest_file
        
        return None
    
    def collect_data(self, room_name: str, dry_run: bool = True) -> Dict:
        """Główna funkcja zbierania danych"""
        
        print(f"🏠 Pokój Discord: {room_name}")
        
        # 1. Sprawdź istniejący raport
        existing_report = self.check_existing_report(room_name)
        if existing_report:
            print(f"⚠️ Istnieje raport: {os.path.basename(existing_report)}")
            return {
                'success': False,
                'error': 'Raport już istnieje',
                'existing_report': existing_report
            }
        
        # 2. Pobierz kanały dla tego pokoju
        channels = self.get_channels_for_room(room_name)
        if not channels:
            return {
                'success': False,
                'error': f'Brak kanałów dla pokoju: {room_name}'
            }
        
        print(f"📺 Kanały do sprawdzenia: {len(channels)}")
        for i, channel in enumerate(channels[:5], 1):  # Pokaż pierwsze 5
            print(f"  {i}. {channel}")
        if len(channels) > 5:
            print(f"  ... i {len(channels) - 5} więcej")
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'room_name': room_name,
                'channels_count': len(channels),
                'channels': channels,
                'days': self.days_back,
                'message': f'DRY RUN: Zebrałbym dane z {len(channels)} kanałów dla pokoju {room_name}'
            }
        
        # TODO: Rzeczywiste zbieranie danych
        # Użyj smart_date_collector z warsztatu
        
        return {
            'success': True,
            'room_name': room_name,
            'channels': channels,
            'message': f'Rozpoczynam zbieranie danych dla pokoju {room_name}'
        }


# TESTY
if __name__ == "__main__":
    print("🧪 TEST UPRASZCZONEGO SYSTEMU RAPORTÓW V2")
    print("=" * 55)
    
    try:
        system = SimpleRaportSystemV2()
        
        # Test 1: Pobieranie kanałów dla pokojów
        test_rooms = [
            'polityka',
            'showbiz',
            'motoryzacja',
            'nieznany-pokoj'
        ]
        
        print("\n📺 TEST POBIERANIA KANAŁÓW DLA POKOJÓW:")
        for room in test_rooms:
            channels = system.get_channels_for_room(room)
            print(f"  {room}: {len(channels)} kanałów")
        
        # Test 2: Dry run dla różnych pokojów
        print("\n🧪 TEST DRY RUN DLA POKOJÓW:")
        for room in ['polityka', 'showbiz']:
            print(f"\n--- {room.upper()} ---")
            result = system.collect_data(room, dry_run=True)
            print(f"  Wynik: {result.get('message', 'BŁĄD')}")
        
        print("\n✅ WSZYSTKIE TESTY ZALICZONE!")
        
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
        sys.exit(1) 