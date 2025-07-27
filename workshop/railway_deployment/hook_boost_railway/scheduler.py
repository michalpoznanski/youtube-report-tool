#!/usr/bin/env python3
"""
SCHEDULER - AUTOMATYCZNE CODZIENNE RAPORTY
===========================================

Uruchamia codziennie o 6:00 rano zbieranie danych ze wszystkich pokojów.
Dla Railway.app deployment.
"""

import os
import sys
import asyncio
import schedule
import time
from datetime import datetime, timezone

# Dodaj ścieżkę do modułów
sys.path.append('.')

from raport_system_workshop import RaportSystemWorkshop
from quota_manager import QuotaManager

class AutoScheduler:
    """Automatyczny scheduler dla codziennych raportów"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.quota_manager = QuotaManager(self.api_key)
        
        # Pokoje do monitorowania
        self.rooms = ['showbiz', 'polityka', 'motoryzacja', 'podcast', 'ai', 'ciekawostki-filmy']
        
        print(f"🤖 AutoScheduler uruchomiony")
        print(f"📺 Pokoje: {', '.join(self.rooms)}")
    
    def daily_collection(self):
        """Codzienna kolekcja danych ze wszystkich pokojów"""
        print(f"\n🌅 CODZIENNA KOLEKCJA - {datetime.now(timezone.utc)}")
        print("=" * 50)
        
        total_quota = 0
        total_videos = 0
        
        for room in self.rooms:
            try:
                print(f"\n🔄 Przetwarzam pokój: {room}")
                
                # Inicjalizuj system (PRAWDZIWY, nie demo!)
                raport_system = RaportSystemWorkshop(
                    api_key=self.api_key,
                    quota_manager=self.quota_manager,
                    demo_mode=False  # PRAWDZIWE API CALLS!
                )
                
                # Zbierz dane
                result = raport_system.collect_room_data(room)
                
                if result['success']:
                    print(f"✅ {room}: {result['videos_collected']} filmów, {result['quota_used']} quota")
                    total_quota += result['quota_used']
                    total_videos += result['videos_collected']
                else:
                    print(f"❌ {room}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Błąd dla {room}: {e}")
        
        print(f"\n🎉 KOLEKCJA ZAKOŃCZONA!")
        print(f"📊 Łącznie: {total_videos} filmów")
        print(f"⛽ Quota użyte: {total_quota}")
        print("=" * 50)
    
    def start_scheduler(self):
        """Uruchamia scheduler"""
        # Codzienny raport o 6:00
        schedule.every().day.at("06:00").do(self.daily_collection)
        
        # Test - co minutę (do debugowania)
        # schedule.every().minute.do(self.daily_collection)
        
        print(f"⏰ Scheduler skonfigurowany: codziennie o 6:00")
        print(f"🔄 Uruchamiam pętlę...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Sprawdzaj co minutę

if __name__ == "__main__":
    scheduler = AutoScheduler()
    scheduler.start_scheduler() 