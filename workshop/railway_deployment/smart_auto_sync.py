#!/usr/bin/env python3
"""
SMART AUTO SYNC - INTELIGENTNY SYSTEM
=====================================

Łączy automatyczną synchronizację z kontrolą Railway
"""

import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from railway_sync_v2 import RailwaySyncV2
from railway_controller import RailwayController

class SmartAutoSync(FileSystemEventHandler):
    """Inteligentny system auto sync z kontrolą Railway"""
    
    def __init__(self, github_token, railway_token=None):
        self.github_token = github_token
        self.railway_token = railway_token
        
        # Inicjalizuj komponenty
        self.sync = RailwaySyncV2(github_token=github_token)
        self.railway = RailwayController(railway_token=railway_token)
        
        self.last_sync = 0
        self.sync_cooldown = 30  # sekundy między syncami
        self.auto_restart = True  # automatyczny restart po sync
        
        # Pliki do monitorowania
        self.watch_files = [
            "main.py",
            "raport_system_workshop.py", 
            "sledz_system.py",
            "quota_manager.py",
            "channels_config.json",
            "requirements.txt",
            "Dockerfile",
            "railway.json",
            "scheduler.py"
        ]
        
        print("🧠 Smart Auto Sync uruchomiony!")
        print(f"📁 Monitoruję: {len(self.watch_files)} plików")
        print(f"⏱️ Cooldown: {self.sync_cooldown} sekund")
        print(f"🔄 Auto restart: {'TAK' if self.auto_restart else 'NIE'}")
    
    def on_modified(self, event):
        """Gdy plik zostanie zmodyfikowany"""
        if event.is_directory:
            return
        
        file_name = Path(event.src_path).name
        if file_name in self.watch_files:
            current_time = time.time()
            
            # Sprawdź cooldown
            if current_time - self.last_sync < self.sync_cooldown:
                print(f"⏳ Cooldown aktywny, pomijam sync dla {file_name}")
                return
            
            print(f"\n🔄 Wykryto zmianę: {file_name}")
            print("🚀 Inteligentna synchronizacja...")
            
            try:
                # 1. Sync z GitHub
                print("📤 Synchronizuję z GitHub...")
                success = self.sync.quick_sync(file_name, f"Smart auto sync: {file_name}")
                
                if success:
                    print(f"✅ Sync zakończony dla {file_name}")
                    self.last_sync = current_time
                    
                    # 2. Automatyczny restart Railway (jeśli włączony)
                    if self.auto_restart:
                        print("🚂 Restartuję Railway serwer...")
                        restart_success = self.railway.restart_service()
                        
                        if restart_success:
                            print("✅ Railway serwer zrestartowany!")
                        else:
                            print("⚠️ Błąd restartu Railway (może brak tokenu)")
                    else:
                        print("⏸️ Auto restart wyłączony")
                        
                else:
                    print(f"❌ Błąd sync dla {file_name}")
                    
            except Exception as e:
                print(f"❌ Błąd podczas inteligentnej sync: {e}")
    
    def manual_sync_and_restart(self, file_name=None):
        """Ręczna synchronizacja i restart"""
        print("🔄 Ręczna synchronizacja i restart...")
        
        try:
            # 1. Sync
            if file_name:
                success = self.sync.quick_sync(file_name, f"Manual sync: {file_name}")
            else:
                success = self.sync.sync_to_railway_auto("Manual full sync")
            
            if success:
                print("✅ Synchronizacja zakończona")
                
                # 2. Restart
                if self.auto_restart:
                    print("🚂 Restartuję Railway...")
                    restart_success = self.railway.restart_service()
                    
                    if restart_success:
                        print("✅ Railway zrestartowany!")
                        return True
                    else:
                        print("⚠️ Błąd restartu Railway")
                        return False
                else:
                    print("✅ Synchronizacja zakończona (bez restartu)")
                    return True
            else:
                print("❌ Błąd synchronizacji")
                return False
                
        except Exception as e:
            print(f"❌ Błąd ręcznej sync: {e}")
            return False

def start_smart_auto_sync():
    """Uruchamia inteligentny auto sync"""
    
    # Tokens
    GITHUB_TOKEN = "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"
    RAILWAY_TOKEN = "01cb5053-0fac-4ffe-9618-c7af6466902d"
    
    # Ścieżka do warsztatu
    workshop_path = Path("/Users/maczek/Desktop/BOT/workshop/railway_deployment/hook_boost_railway")
    
    if not workshop_path.exists():
        print(f"❌ Warsztat nie istnieje: {workshop_path}")
        return
    
    # Inicjalizuj smart sync
    smart_sync = SmartAutoSync(GITHUB_TOKEN, RAILWAY_TOKEN)
    observer = Observer()
    observer.schedule(smart_sync, str(workshop_path), recursive=False)
    
    print(f"👁️ Rozpoczynam inteligentne monitorowanie: {workshop_path}")
    print("🔄 Automatyczna synchronizacja + restart aktywny!")
    print("⏹️ Naciśnij Ctrl+C aby zatrzymać")
    print("\n🎯 KOMENDY:")
    print("- smart_sync.manual_sync_and_restart() - ręczna sync + restart")
    print("- smart_sync.manual_sync_and_restart('main.py') - sync konkretnego pliku")
    
    try:
        observer.start()
        
        # Dodaj smart_sync do global scope dla interaktywnego użycia
        globals()['smart_sync'] = smart_sync
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n⏹️ Smart Auto Sync zatrzymany")
    
    observer.join()

if __name__ == "__main__":
    start_smart_auto_sync() 