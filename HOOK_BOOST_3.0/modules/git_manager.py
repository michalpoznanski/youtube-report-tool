#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GIT MANAGER - HOOK BOOST 3.0
============================

Automatyczne commitowanie raportów do GitHub.
"""

import os
import subprocess
import json
from datetime import datetime, timezone

class GitManager:
    """Zarządzanie Git dla Hook Boost 3.0"""
    
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        print(f"🔗 GitManager: {os.path.abspath(repo_path)}")
    
    def setup_git(self):
        """Konfiguruje Git repo"""
        try:
            # Sprawdź czy to jest Git repo
            result = subprocess.run(
                ['git', 'status'], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print("❌ To nie jest Git repository")
                return False
            
            # Sprawdź remote origin
            remote_result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if remote_result.returncode != 0:
                # Dodaj remote origin z tokenem
                remote_url = f"https://{self.github_token}@github.com/michalpoznanski/hookboost.git"
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', remote_url],
                    cwd=self.repo_path
                )
                print("✅ Remote origin dodany")
            else:
                print("✅ Remote origin już istnieje")
            
            # Konfiguruj Git (jeśli ma token)
            if self.github_token:
                subprocess.run(
                    ['git', 'config', 'user.name', 'Hook Boost 3.0'],
                    cwd=self.repo_path
                )
                subprocess.run(
                    ['git', 'config', 'user.email', 'hookboost@example.com'],
                    cwd=self.repo_path
                )
            
            print("✅ Git repository skonfigurowane")
            return True
            
        except Exception as e:
            print(f"❌ Błąd konfiguracji Git: {e}")
            return False
    
    def commit_reports(self, message=None):
        """Commituje raporty do Git"""
        try:
            if not message:
                message = f"Auto-commit raportów Hook Boost 3.0 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
            
            # Dodaj wszystkie pliki CSV
            subprocess.run(
                ['git', 'add', 'data/raw_data/'],
                cwd=self.repo_path
            )
            
            # Sprawdź czy są zmiany
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print("ℹ️ Brak zmian do commitowania")
                return True
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path
            )
            
            print(f"✅ Zcommitowano: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd commitowania: {e}")
            return False
    
    def push_to_github(self):
        """Pushuje zmiany do GitHub"""
        try:
            if not self.github_token:
                print("⚠️ Brak GITHUB_TOKEN - push nie jest możliwy")
                return False
            
            # Push do main branch
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Push do GitHub zakończony")
                return True
            else:
                print(f"❌ Błąd push: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Błąd push: {e}")
            return False
    
    def auto_commit_and_push(self, message=None):
        """Automatyczny commit i push"""
        print(f"🔗 GitManager: Rozpoczynam auto-commit i push")
        print(f"🔗 GitManager: Token: {'✅ Ustawiony' if self.github_token else '❌ BRAK'}")
        
        if not self.setup_git():
            print("❌ GitManager: Błąd setup_git")
            return False
            
        if not self.commit_reports(message):
            print("❌ GitManager: Błąd commit_reports")
            return False
            
        result = self.push_to_github()
        print(f"🔗 GitManager: Push result: {result}")
        return result 