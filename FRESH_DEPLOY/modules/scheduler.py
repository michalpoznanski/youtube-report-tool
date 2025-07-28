#!/usr/bin/env python3
"""
SCHEDULER - HOOK BOOST 3.0
==========================

Automatyczne codzienne raporty dla Hook Boost 3.0.
Ultra lean mode - bez QuotaManager.

AUTOR: Hook Boost 3.0 - Ultra Lean
WERSJA: 3.0 (Scheduler)
"""

import os
import sys
import schedule
import time
from datetime import datetime, timezone

# Dodaj ścieżkę do modułów
sys.path.append('.')

from modules.raport_system import RaportSystem
from modules.config_manager import ConfigManager
from modules.git_manager import GitManager

class AutoScheduler:
    """Automatyczny scheduler dla codziennych raportów"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            print("❌ Brak YOUTUBE_API_KEY - scheduler nie może działać")
            return
        
        # Inicjalizuj systemy
        self.config_manager = ConfigManager()
        self.raport_system = RaportSystem(api_key=self.api_key)
        self.git_manager = GitManager()
        
        # Pobierz wszystkie pokoje z konfiguracji
        self.rooms = self._get_active_rooms()
        
        print(f"🤖 AutoScheduler Hook Boost 3.0 uruchomiony")
        print(f"📺 Aktywne pokoje: {', '.join(self.rooms)}")
        print(f"⚡ Ultra lean mode - bez QuotaManager")
    
    def _get_active_rooms(self):
        """Pobiera aktywne pokoje z konfiguracji"""
        config = self.config_manager.load_channels_config()
        rooms = []
        
        for room_name, channels in config.get('channels', {}).items():
            if channels:  # Tylko pokoje z kanałami
                rooms.append(room_name)
        
        return rooms
    
    def daily_collection(self):
        """Codzienna kolekcja danych ze wszystkich pokojów"""
        print(f"\n🌅 CODZIENNA KOLEKCJA HOOK BOOST 3.0 - {datetime.now(timezone.utc)}")
        print("=" * 60)
        
        total_videos = 0
        successful_rooms = 0
        
        # Odśwież listę pokojów (może ktoś dodał nowe)
        self.rooms = self._get_active_rooms()
        
        if not self.rooms:
            print("⚠️ Brak aktywnych pokojów z kanałami")
            return
        
        for room in self.rooms:
            try:
                print(f"\n🔄 Przetwarzam pokój: {room}")
                
                # Pobierz kanały dla pokoju
                channels = self.config_manager.get_room_channels(room)
                
                if not channels:
                    print(f"⚠️ Pokój {room}: brak kanałów")
                    continue
                
                # Generuj raport
                result = self.raport_system.generate_room_report(room, channels)
                
                if result['success']:
                    print(f"✅ {room}: {result['videos']} filmów, {result['channels']} kanałów")
                    print(f"📁 Plik: {result['filename']}")
                    total_videos += result['videos']
                    successful_rooms += 1
                else:
                    print(f"❌ {room}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Błąd dla {room}: {e}")
        
        print(f"\n🎉 KOLEKCJA ZAKOŃCZONA!")
        print(f"📊 Pokoje: {successful_rooms}/{len(self.rooms)}")
        print(f"📺 Filmy: {total_videos}")
        print(f"⚡ Ultra lean mode - quota nie monitorowane")
        print("=" * 60)
        
        # Auto-commit do GitHub
        if successful_rooms > 0:
            print(f"\n🔗 Auto-commit do GitHub...")
            self.git_manager.auto_commit_and_push("Codzienne raporty Hook Boost 3.0")
    
    def start_scheduler(self):
        """Uruchamia scheduler"""
        # Codzienny raport o 6:00 UTC
        schedule.every().day.at("06:00").do(self.daily_collection)
        
        # Test - co 5 minut (do debugowania)
        # schedule.every(5).minutes.do(self.daily_collection)
        
        print(f"⏰ Scheduler skonfigurowany: codziennie o 6:00 UTC")
        print(f"🔄 Uruchamiam pętlę...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Sprawdzaj co minutę

if __name__ == "__main__":
    scheduler = AutoScheduler()
    scheduler.start_scheduler() 