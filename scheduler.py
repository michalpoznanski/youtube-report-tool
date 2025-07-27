#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⏰ SCHEDULER - ULTRA LEAN VERSION
================================

Ultra-lekki scheduler dla codziennych raportów:
- Automatyczne raporty o 06:00 UTC
- Multi-room support
- Bez quota managera
- Tylko surowe CSV raporty

AUTOR: Hook Boost V2 - Ultra Lean Edition
WERSJA: 3.0 (Railway Ready)
"""

import os
import schedule
import time
from datetime import datetime
from raport_system_workshop import RaportSystemWorkshop

class AutoScheduler:
    """Ultra lean scheduler dla automatycznych raportów"""
    
    def __init__(self):
        """Inicjalizacja schedulera"""
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ YOUTUBE_API_KEY not found in environment variables")
        
        # Lista pokojów do raportowania
        self.rooms = [
            'showbiz',
            'polityka', 
            'motoryzacja',
            'podcast',
            'ai',
            'ciekawostki-filmy'
        ]
        
        print("⏰ AutoScheduler Ultra Lean initialized")
        print(f"   Rooms to monitor: {len(self.rooms)}")
        print(f"   Schedule: Daily at 06:00 UTC")
    
    def daily_collection(self):
        """Wykonuje codzienne zbieranie danych dla wszystkich pokojów"""
        print(f"🚀 Starting daily collection at {datetime.now()}")
        
        # Inicjalizuj system raportów - ULTRA LEAN
        raport_system = RaportSystemWorkshop(
            api_key=self.api_key,
            quota_manager=None,  # BEZ QUOTA MANAGERA
            demo_mode=False      # PRODUKCJA
        )
        
        successful_reports = 0
        failed_reports = 0
        
        for room in self.rooms:
            try:
                print(f"📊 Processing room: {room}")
                
                result = raport_system.collect_room_data(room)
                
                if result['success']:
                    print(f"✅ {room}: {result['videos_collected']} videos, {result['channels_processed']} channels")
                    successful_reports += 1
                else:
                    print(f"❌ {room}: {result.get('error', 'Unknown error')}")
                    failed_reports += 1
                    
            except Exception as e:
                print(f"❌ {room}: Exception - {str(e)}")
                failed_reports += 1
        
        print(f"📈 Daily collection completed:")
        print(f"   ✅ Successful: {successful_reports}")
        print(f"   ❌ Failed: {failed_reports}")
        print(f"   📅 Timestamp: {datetime.now()}")
    
    def start_scheduler(self):
        """Uruchamia scheduler"""
        print("⏰ Setting up daily schedule...")
        
        # Zaplanuj codzienne raporty o 06:00 UTC
        schedule.every().day.at("06:00").do(self.daily_collection)
        
        print("✅ Scheduler started - daily reports at 06:00 UTC")
        print("🔄 Waiting for scheduled tasks...")
        
        # Główna pętla schedulera
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Sprawdzaj co minutę
            except KeyboardInterrupt:
                print("\n⏹️ Scheduler stopped by user")
                break
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(300)  # Poczekaj 5 minut przy błędzie

if __name__ == "__main__":
    """Uruchomienie schedulera"""
    print("🚀 Hook Boost Ultra Lean Scheduler")
    print("==================================")
    
    try:
        scheduler = AutoScheduler()
        scheduler.start_scheduler()
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}") 