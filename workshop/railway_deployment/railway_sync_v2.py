#!/usr/bin/env python3
"""
RAILWAY SYNC V2 - AUTOMATYCZNY GIT PUSH
======================================

Ulepszona wersja Railway Sync z:
- Automatycznym git push
- Inicjalizacją lokalnego repo
- Sync bez ręcznego upload

AUTOR: Hook Boost V2 Railway Integration
"""

import os
import shutil
import json
import subprocess
from datetime import datetime
from pathlib import Path

class RailwaySyncV2:
    """Ulepszona synchronizacja z Railway z auto git push"""
    
    def __init__(self, github_token=None):
        self.workshop_path = Path("/Users/maczek/Desktop/BOT/workshop/railway_deployment/hook_boost_railway")
        self.main_path = Path("/Users/maczek/Desktop/BOT")
        
        # GitHub token (jeśli podany)
        self.github_token = github_token
        if github_token:
            # Użyj HTTPS z tokenem
            self.github_repo = f"https://{github_token}@github.com/michalpoznanski/hookboost.git"
        else:
            self.github_repo = "https://github.com/michalpoznanski/hookboost.git"
        
        # Lokalne git repo (klone GitHub repo)
        self.local_git_path = Path("/Users/maczek/Desktop/hookboost_local_git")
        
        print("🚂 Railway Sync V2 uruchomiony")
        print(f"📁 Warsztat: {self.workshop_path}")
        print(f"🏠 Główny projekt: {self.main_path}")
        print(f"📦 Lokalne Git: {self.local_git_path}")
    
    def setup_local_git(self):
        """Inicjalizuje lokalne git repo"""
        print("\n📦 SETUP LOKALNEGO GIT REPO")
        print("=" * 40)
        
        try:
            # Jeśli folder istnieje, sprawdź czy to git repo
            if self.local_git_path.exists():
                git_dir = self.local_git_path / ".git"
                if git_dir.exists():
                    print(f"✅ Git repo już istnieje w {self.local_git_path}")
                    return True
                else:
                    # Usuń folder jeśli nie jest git repo
                    shutil.rmtree(self.local_git_path)
            
            # Klonuj repo (bez tokenu, bo już działa)
            subprocess.run([
                "git", "clone", "https://github.com/michalpoznanski/hookboost.git", str(self.local_git_path)
            ], check=True, capture_output=True)
            
            print(f"✅ Repo sklonowane do {self.local_git_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd klonowania: {e}")
            return False
    
    def sync_to_railway_auto(self, files=None, commit_message=None):
        """
        Automatyczna synchronizacja z git push
        
        Args:
            files: Lista plików do sync (None = wszystkie)
            commit_message: Wiadomość commit
        """
        print("\n🚀 AUTOMATYCZNA SYNCHRONIZACJA → RAILWAY")
        print("=" * 50)
        
        # Setup git repo jeśli nie istnieje
        if not self.local_git_path.exists():
            if not self.setup_local_git():
                return False
        
        try:
            # 1. Skopiuj pliki z warsztatu do git repo
            if not files:
                files = [
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
            
            for file in files:
                source = self.workshop_path / file
                target = self.local_git_path / file
                
                if source.exists():
                    shutil.copy2(source, target)
                    print(f"✅ Skopiowano: {file}")
                else:
                    print(f"⚠️ Brak pliku: {file}")
            
            # Dodaj timestamp do main.py żeby zawsze były zmiany
            if "main.py" in files:
                main_py_path = self.local_git_path / "main.py"
                if main_py_path.exists():
                    with open(main_py_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Dodaj timestamp na końcu pliku
                    timestamp = f"\n# Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    if timestamp not in content:
                        with open(main_py_path, 'a', encoding='utf-8') as f:
                            f.write(timestamp)
                        print("⏰ Dodano timestamp do main.py")
            
            # 2. Git add, commit, push
            if not commit_message:
                commit_message = f"Auto sync - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Zmień directory na git repo
            original_cwd = os.getcwd()
            os.chdir(self.local_git_path)
            
            # Sprawdź status i zsynchronizuj z origin
            try:
                # Sprawdź czy są lokalne commity do wypchnięcia
                result = subprocess.run(["git", "log", "--oneline", "origin/main..HEAD"], capture_output=True, text=True)
                if result.stdout.strip():
                    print("📤 Wypycham lokalne commity...")
                    # Użyj tokenu w URL dla push
                    push_url = f"https://{self.github_token}@github.com/michalpoznanski/hookboost.git"
                    subprocess.run(["git", "push", push_url, "main"], check=True, capture_output=True)
                
                # Pull najpierw, żeby zsynchronizować
                subprocess.run(["git", "pull", "origin", "main"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Jeśli pull nie działa, zresetuj do origin
                subprocess.run(["git", "reset", "--hard", "origin/main"], check=True, capture_output=True)
            
            # Git commands
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            # Użyj tokenu w URL dla push
            push_url = f"https://{self.github_token}@github.com/michalpoznanski/hookboost.git"
            subprocess.run(["git", "push", push_url, "main"], check=True)
            
            # Wróć do originalnego directory
            os.chdir(original_cwd)
            
            print(f"\n🎉 AUTOMATYCZNA SYNCHRONIZACJA ZAKOŃCZONA!")
            print(f"📤 Commit: {commit_message}")
            print(f"🚂 Railway automatycznie wykryje zmiany i zrobi redeploy")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd git: {e}")
            return False
        except Exception as e:
            print(f"❌ Błąd synchronizacji: {e}")
            return False
    
    def quick_sync(self, file_name, commit_msg=None):
        """Szybka synchronizacja pojedynczego pliku"""
        if not commit_msg:
            commit_msg = f"Quick sync: {file_name}"
        
        return self.sync_to_railway_auto([file_name], commit_msg)
    
    def sync_config_only(self):
        """Synchronizuj tylko pliki konfiguracyjne"""
        config_files = ["channels_config.json", "quota_usage.json"]
        return self.sync_to_railway_auto(config_files, "Sync config files")
    
    def sync_code_only(self):
        """Synchronizuj tylko kod (bez config)"""
        code_files = ["main.py", "raport_system_workshop.py", "sledz_system.py", "quota_manager.py"]
        return self.sync_to_railway_auto(code_files, "Sync code updates")

# DEMO UŻYCIA
if __name__ == "__main__":
    sync = RailwaySyncV2()
    
    print("\n🎯 DOSTĘPNE OPCJE V2:")
    print("1. sync.setup_local_git() - setup git repo")
    print("2. sync.sync_to_railway_auto() - pełna automatyczna sync")
    print("3. sync.quick_sync('main.py') - szybka sync jednego pliku")
    print("4. sync.sync_config_only() - tylko config")
    print("5. sync.sync_code_only() - tylko kod")
    
    # Test setup
    print("\n🧪 TEST SETUP:")
    if sync.setup_local_git():
        print("✅ Git repo gotowe do automatycznego sync!")
    else:
        print("❌ Problem z setup git repo") 