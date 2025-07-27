#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⏰ SCHEDULER V3 - ULTRA LEAN
==========================

Prosty scheduler codziennych raportów:
- 06:00 UTC
- Multi-room
- Bez quota managera

AUTOR: Hook Boost V3 - Fresh Ultra Lean
WERSJA: 3.0.0 (2025-01-27)
"""

import os
import schedule
import time
from datetime import datetime
from report_generator import ReportGenerator
from channel_manager import ChannelManager

class AutoScheduler:
    """Prosty scheduler V3"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ YOUTUBE_API_KEY missing")
        
        self.rooms = [
            'showbiz',
            'polityka', 
            'motoryzacja',
            'podcast',
            'ai',
            'ciekawostki-filmy'
        ]
        
        print("⏰ AutoScheduler V3 initialized")
    
    def daily_collection(self):
        """Codzienne zbieranie danych"""
        print(f"🚀 Daily collection: {datetime.now()}")
        
        generator = ReportGenerator(self.api_key)
        manager = ChannelManager()
        
        for room in self.rooms:
            try:
                channels = manager.get_channels(room)
                if not channels:
                    print(f"⚠️ {room}: No channels")
                    continue
                
                result = generator.generate_report(room, channels)
                
                if result['success']:
                    print(f"✅ {room}: {result['videos']} videos")
                else:
                    print(f"❌ {room}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ {room}: {e}")
    
    def start_scheduler(self):
        """Start scheduler"""
        schedule.every().day.at("06:00").do(self.daily_collection)
        
        print("✅ Scheduler started - daily at 06:00 UTC")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n⏹️ Scheduler stopped")
                break
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(300)

if __name__ == "__main__":
    scheduler = AutoScheduler()
    scheduler.start_scheduler()
