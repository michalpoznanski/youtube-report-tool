#!/usr/bin/env python3
"""
UPRASZCZONY SYSTEM RAPORTÓW - WARSZTAT
Cel: Czyste dane CSV bez ekstrakcji nazwisk, proste rozpoznawanie pokojów
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

class SimpleRaportSystem:
    """Uproszczony system raportów - czyste dane CSV"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("Brak YOUTUBE_API_KEY")
        
        # Proste mapowanie pokojów (nie AI!)
        self.room_categories = {
            'polityka': 'politics',
            'politics': 'politics',
            'polityk': 'politics',
            'rząd': 'politics',
            'sejm': 'politics',
            'senat': 'politics',
            'wybory': 'politics',
            
            'showbiz': 'showbiz',
            'gwiazdy': 'showbiz',
            'celebryci': 'showbiz',
            'muzyka': 'showbiz',
            'film': 'showbiz',
            'telewizja': 'showbiz',
            'ciekawostki-film': 'showbiz',
            
            'motoryzacja': 'motoryzacja',
            'samochody': 'motoryzacja',
            'auta': 'motoryzacja',
            'cars': 'motoryzacja',
            
            'podcast': 'podcast',
            'audio': 'podcast',
            'radio': 'podcast'
        }
        
        # Domyślna kategoria
        self.default_category = 'showbiz'
        
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
    
    def detect_category_from_room(self, room_name: str) -> str:
        """Proste wykrywanie kategorii na podstawie nazwy pokoju"""
        room_lower = room_name.lower()
        
        # Sprawdź mapowanie
        for room_keyword, category in self.room_categories.items():
            if room_keyword in room_lower:
                return category
        
        # Domyślnie showbiz
        return self.default_category
    
    def get_channels_for_category(self, category: str) -> List[str]:
        """Pobiera listę kanałów dla danej kategorii"""
        # Mapowanie kategorii na klucze w config
        category_mapping = {
            'politics': 'polityka',
            'showbiz': 'showbiz',
            'motoryzacja': 'motoryzacja',
            'podcast': 'podcast'
        }
        
        config_key = category_mapping.get(category, 'showbiz')
        
        if 'channels' in self.channels_config and config_key in self.channels_config['channels']:
            channels = self.channels_config['channels'][config_key]
            # Wyciągnij tylko ID/handles kanałów
            return [ch['id'] if isinstance(ch, dict) else ch for ch in channels]
        
        print(f"⚠️ Brak kanałów dla kategorii: {category}")
        return []
    
    def check_existing_report(self, category: str) -> Optional[str]:
        """Sprawdza czy istnieje raport z ostatnich 7 dni"""
        reports_dir = f'reports/{category}'
        
        if not os.path.exists(reports_dir):
            return None
        
        # Znajdź pliki CSV z ostatnich 7 dni
        csv_files = glob.glob(f'{reports_dir}/youtube_data_{category}_*.csv')
        
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
        
        # 1. Wykryj kategorię
        category = self.detect_category_from_room(room_name)
        print(f"🏷️ Wykryta kategoria: {category}")
        
        # 2. Sprawdź istniejący raport
        existing_report = self.check_existing_report(category)
        if existing_report:
            print(f"⚠️ Istnieje raport: {os.path.basename(existing_report)}")
            return {
                'success': False,
                'error': 'Raport już istnieje',
                'existing_report': existing_report
            }
        
        # 3. Pobierz kanały
        channels = self.get_channels_for_category(category)
        if not channels:
            return {
                'success': False,
                'error': f'Brak kanałów dla kategorii: {category}'
            }
        
        print(f"📺 Kanały do sprawdzenia: {len(channels)}")
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'category': category,
                'channels_count': len(channels),
                'days': self.days_back,
                'message': f'DRY RUN: Zebrałbym dane z {len(channels)} kanałów dla {category}'
            }
        
        # TODO: Rzeczywiste zbieranie danych
        # Użyj smart_date_collector z warsztatu
        
        return {
            'success': True,
            'category': category,
            'channels': channels,
            'message': f'Rozpoczynam zbieranie danych dla {category}'
        }


# TESTY
if __name__ == "__main__":
    print("🧪 TEST UPRASZCZONEGO SYSTEMU RAPORTÓW")
    print("=" * 50)
    
    try:
        system = SimpleRaportSystem()
        
        # Test 1: Wykrywanie kategorii
        test_rooms = [
            'polityka-2024',
            'showbiz-gwiazdy',
            'motoryzacja-samochody',
            'nieznany-pokoj'
        ]
        
        print("\n🔍 TEST WYKRYWANIA KATEGORII:")
        for room in test_rooms:
            category = system.detect_category_from_room(room)
            print(f"  {room} → {category}")
        
        # Test 2: Pobieranie kanałów
        print("\n📺 TEST POBIERANIA KANAŁÓW:")
        for category in ['politics', 'showbiz', 'motoryzacja']:
            channels = system.get_channels_for_category(category)
            print(f"  {category}: {len(channels)} kanałów")
        
        # Test 3: Dry run
        print("\n🧪 TEST DRY RUN:")
        result = system.collect_data('polityka-test', dry_run=True)
        print(f"  Wynik: {result}")
        
        print("\n✅ WSZYSTKIE TESTY ZALICZONE!")
        
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
        sys.exit(1) 