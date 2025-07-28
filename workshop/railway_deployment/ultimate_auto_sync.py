#!/usr/bin/env python3
"""
ULTIMATE AUTO SYNC - OSTATECZNE ROZWIĄZANIE
==========================================

Automatyczna synchronizacja z GitHub + Railway auto redeploy
"""

import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from railway_sync_v2 import RailwaySyncV2

class UltimateAutoSync(FileSystemEventHandler):
    """Ostateczny system auto sync"""
    
    def __init__(self, github_token):
        self.github_token = github_token
        self.sync = RailwaySyncV2(github_token=github_token)
        
        self.last_sync = 0
        self.sync_cooldown = 30  # sekundy między syncami
        self.sync_count = 0
        
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
        
        print("🚀 ULTIMATE AUTO SYNC uruchomiony!")
        print(f"📁 Monitoruję: {len(self.watch_files)} plików")
        print(f"⏱️ Cooldown: {self.sync_cooldown} sekund")
        print(f"🔄 Railway auto redeploy: AKTYWNY")
        print(f"📊 Licznik sync: {self.sync_count}")
    
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
            print("🚀 ULTIMATE synchronizacja...")
            
            try:
                # Sync z GitHub
                print("📤 Synchronizuję z GitHub...")
                success = self.sync.quick_sync(file_name, f"Ultimate auto sync #{self.sync_count + 1}: {file_name}")
                
                if success:
                    self.sync_count += 1
                    self.last_sync = current_time
                    print(f"✅ Sync #{self.sync_count} zakończony dla {file_name}")
                    print("🚂 Railway automatycznie wykryje zmiany i zrobi redeploy!")
                    print(f"📊 Łącznie synców: {self.sync_count}")
                else:
                    print(f"❌ Błąd sync dla {file_name}")
                    
            except Exception as e:
                print(f"❌ Błąd podczas ultimate sync: {e}")
    
    def manual_sync(self, file_name=None, message=None):
        """Ręczna synchronizacja"""
        print("🔄 Ręczna synchronizacja...")
        
        try:
            if file_name:
                success = self.sync.quick_sync(file_name, message or f"Manual sync: {file_name}")
            else:
                success = self.sync.sync_to_railway_auto(message or "Manual full sync")
            
            if success:
                self.sync_count += 1
                print(f"✅ Ręczna sync #{self.sync_count} zakończona")
                print("🚂 Railway automatycznie wykryje zmiany!")
                return True
            else:
                print("❌ Błąd ręcznej synchronizacji")
                return False
                
        except Exception as e:
            print(f"❌ Błąd ręcznej sync: {e}")
            return False
    
    def get_stats(self):
        """Pobiera statystyki"""
        return {
            "sync_count": self.sync_count,
            "last_sync": self.last_sync,
            "cooldown": self.sync_cooldown
        }

def start_ultimate_auto_sync():
    """Uruchamia ultimate auto sync"""
    
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
    
    # Inicjalizuj ultimate sync
    ultimate_sync = UltimateAutoSync(GITHUB_TOKEN)
    observer = Observer()
    observer.schedule(ultimate_sync, str(workshop_path), recursive=False)
    
    print(f"👁️ Rozpoczynam ULTIMATE monitorowanie: {workshop_path}")
    print("🔄 Automatyczna synchronizacja + Railway auto redeploy AKTYWNY!")
    print("⏹️ Naciśnij Ctrl+C aby zatrzymać")
    print("\n🎯 KOMENDY:")
    print("- ultimate_sync.manual_sync() - ręczna pełna sync")
    print("- ultimate_sync.manual_sync('main.py') - sync konkretnego pliku")
    print("- ultimate_sync.get_stats() - statystyki")
    
    try:
        observer.start()
        
        # Dodaj ultimate_sync do global scope dla interaktywnego użycia
        globals()['ultimate_sync'] = ultimate_sync
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        stats = ultimate_sync.get_stats()
        print(f"\n⏹️ Ultimate Auto Sync zatrzymany")
        print(f"📊 Statystyki: {stats['sync_count']} synców wykonanych")
    
    observer.join()

if __name__ == "__main__":
    start_ultimate_auto_sync() 