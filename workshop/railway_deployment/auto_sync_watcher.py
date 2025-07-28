#!/usr/bin/env python3
"""
AUTOMATYCZNY WATCHER - SYNC Z WARSZTATU
=======================================

Automatycznie monitoruje zmiany w warsztacie i syncuje z Railway
"""

import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from railway_sync_v2 import RailwaySyncV2

class WorkshopWatcher(FileSystemEventHandler):
    """Monitoruje zmiany w warsztacie i automatycznie syncuje"""
    
    def __init__(self, github_token):
        self.github_token = github_token
        self.sync = RailwaySyncV2(github_token=github_token)
        self.last_sync = 0
        self.sync_cooldown = 30  # sekundy między syncami
        
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
        
        print("👁️ Automatyczny watcher uruchomiony!")
        print(f"📁 Monitoruję: {len(self.watch_files)} plików")
        print(f"⏱️ Cooldown: {self.sync_cooldown} sekund")
    
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
            print("🚀 Automatyczna synchronizacja...")
            
            try:
                # Sync tylko zmienionego pliku
                success = self.sync.quick_sync(file_name, f"Auto sync: {file_name}")
                
                if success:
                    print(f"✅ Automatyczna sync zakończona dla {file_name}")
                    self.last_sync = current_time
                else:
                    print(f"❌ Błąd automatycznej sync dla {file_name}")
                    
            except Exception as e:
                print(f"❌ Błąd podczas automatycznej sync: {e}")

def start_auto_sync():
    """Uruchamia automatyczny watcher"""
    
    # GitHub token
    # 🛡️ BEZPIECZEŃSTWO: Token usunięty!
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        raise ValueError("❌ Brak GITHUB_TOKEN w zmiennych środowiskowych!")
    
    # Ścieżka do warsztatu
    workshop_path = Path("/Users/maczek/Desktop/BOT/workshop/railway_deployment/hook_boost_railway")
    
    if not workshop_path.exists():
        print(f"❌ Warsztat nie istnieje: {workshop_path}")
        return
    
    # Inicjalizuj watcher
    event_handler = WorkshopWatcher(GITHUB_TOKEN)
    observer = Observer()
    observer.schedule(event_handler, str(workshop_path), recursive=False)
    
    print(f"👁️ Rozpoczynam monitorowanie: {workshop_path}")
    print("🔄 Automatyczna synchronizacja aktywna!")
    print("⏹️ Naciśnij Ctrl+C aby zatrzymać")
    
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n⏹️ Watcher zatrzymany")
    
    observer.join()

if __name__ == "__main__":
    start_auto_sync() 