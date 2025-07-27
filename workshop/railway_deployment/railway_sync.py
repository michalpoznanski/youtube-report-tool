#!/usr/bin/env python3
"""
RAILWAY SYNC SYSTEM
==================

Automatyczna synchronizacja między lokalnym kodem a Railway deployment:
- Push lokalnych zmian → GitHub → Railway
- Pobieranie konfiguracji z Railway
- Backup i restore danych

AUTOR: Hook Boost V2 Railway Integration
"""

import os
import shutil
import json
import subprocess
from datetime import datetime
from pathlib import Path

class RailwaySync:
    """System synchronizacji z Railway"""
    
    def __init__(self):
        self.workshop_path = Path("/Users/maczek/Desktop/BOT/workshop/railway_deployment/hook_boost_railway")
        self.main_path = Path("/Users/maczek/Desktop/BOT")
        self.github_repo = "https://github.com/michalpozanski/hookboost.git"
        
        print("🚂 Railway Sync System uruchomiony")
        print(f"📁 Warsztat: {self.workshop_path}")
        print(f"🏠 Główny projekt: {self.main_path}")
    
    def sync_to_railway(self, files=None):
        """
        Synchronizuje kod lokalny → Railway
        
        Args:
            files: Lista plików do sync (None = wszystkie)
        """
        print("\n📤 SYNC LOKALNY → RAILWAY")
        print("=" * 40)
        
        try:
            # 1. Skopiuj pliki z głównego projektu do warsztatu
            if not files:
                files = [
                    "hook_boost_v2.py",
                    "sledz_system.py", 
                    "quota_manager.py",
                    "channels_config.json",
                    "quota_usage.json"
                ]
            
            for file in files:
                source = self.main_path / file
                target = self.workshop_path / file.replace("hook_boost_v2.py", "main.py")
                
                if source.exists():
                    shutil.copy2(source, target)
                    print(f"✅ Skopiowano: {file}")
                else:
                    print(f"⚠️ Brak pliku: {file}")
            
            # 2. Automatyczny git push (jeśli masz GitHub Desktop)
            self._auto_git_push()
            
            print("\n🎉 Synchronizacja zakończona!")
            print("Railway automatycznie wykryje zmiany i zrobi redeploy")
            
        except Exception as e:
            print(f"❌ Błąd synchronizacji: {e}")
    
    def _auto_git_push(self):
        """Automatyczny git push (wymaga GitHub Desktop)"""
        try:
            # Sprawdź czy GitHub Desktop jest dostępny
            github_desktop = "/Applications/GitHub Desktop.app"
            if os.path.exists(github_desktop):
                print("📤 Używając GitHub Desktop do push...")
                # Otwórz GitHub Desktop (użytkownik musi ręcznie commit+push)
                subprocess.run(["open", "-a", "GitHub Desktop"])
                print("✅ GitHub Desktop otwarty - zrób commit i push ręcznie")
            else:
                print("⚠️ GitHub Desktop nie znaleziony - wgraj pliki ręcznie")
                
        except Exception as e:
            print(f"⚠️ Nie można otworzyć GitHub Desktop: {e}")
    
    def get_railway_config(self):
        """
        Pobiera konfigurację z Railway (symulacja)
        W przyszłości: API call do Railway
        """
        print("\n📥 POBIERANIE KONFIGURACJI Z RAILWAY")
        print("=" * 40)
        
        print("⚠️ Funkcja w rozwoju")
        print("Tymczasowo: sprawdź Railway Logs i skopiuj channels_config ręcznie")
    
    def backup_local(self):
        """Backup lokalnych plików przed sync"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_dir = self.main_path / f"backup/backup_before_railway_sync_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        important_files = [
            "hook_boost_v2.py",
            "sledz_system.py",
            "quota_manager.py", 
            "channels_config.json",
            "quota_usage.json"
        ]
        
        for file in important_files:
            source = self.main_path / file
            if source.exists():
                shutil.copy2(source, backup_dir / file)
        
        print(f"✅ Backup utworzony: {backup_dir}")
        return backup_dir

# DEMO UŻYCIA
if __name__ == "__main__":
    sync = RailwaySync()
    
    print("\n🎯 DOSTĘPNE OPCJE:")
    print("1. sync.sync_to_railway() - wyślij kod na Railway")
    print("2. sync.backup_local() - backup przed zmianami")
    print("3. sync.get_railway_config() - pobierz config z Railway")
    
    # Przykład użycia
    print("\n📋 PRZYKŁAD:")
    print("sync.backup_local()")
    print("sync.sync_to_railway(['hook_boost_v2.py', 'sledz_system.py'])") 