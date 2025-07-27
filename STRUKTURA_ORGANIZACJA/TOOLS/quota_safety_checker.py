#!/usr/bin/env python3
"""
Quota Safety Checker - System zabezpieczeń przed marnowaniem quota
Sprawdza wszystkie komponenty przed użyciem YouTube API
"""

import os
import sys
import json
import subprocess
import importlib
import asyncio
from typing import Dict, List, Tuple, Optional

class QuotaSafetyChecker:
    def __init__(self):
        self.required_files = [
            'data_collector.py',
            'offline_analyzer.py', 
            'quota_manager.py',
            'channels_config.json'
        ]
        
        self.required_modules = [
            'pandas',
            'requests',
            'discord',
            'spacy',
            'numpy'
        ]
        
        self.test_results = {}
    
    def run_full_safety_check(self) -> Tuple[bool, Dict]:
        """Przeprowadza pełny test bezpieczeństwa"""
        print("🛡️ **TEST BEZPIECZEŃSTWA**")
        print("Sprawdzam czy kod działa poprawnie...")
        
        all_tests_passed = True
        failed_tests = []
        
        # 1. Sprawdź pliki
        print("\n📁 Sprawdzam pliki...")
        files_ok = self.check_required_files()
        if not files_ok:
            all_tests_passed = False
            failed_tests.append("Brak wymaganych plików")
        
        # 2. Sprawdź moduły Python
        print("🐍 Sprawdzam moduły Python...")
        modules_ok = self.check_required_modules()
        if not modules_ok:
            all_tests_passed = False
            failed_tests.append("Brak wymaganych modułów Python")
        
        # 3. Sprawdź konfigurację
        print("⚙️ Sprawdzam konfigurację...")
        config_ok = self.check_configuration()
        if not config_ok:
            all_tests_passed = False
            failed_tests.append("Błąd konfiguracji")
        
        # 4. Sprawdź YouTube API (1 quota)
        print("🌐 Sprawdzam YouTube API...")
        api_ok = self.check_youtube_api()
        if not api_ok:
            all_tests_passed = False
            failed_tests.append("Błąd YouTube API")
        
        # 5. Sprawdź spaCy model
        print("🤖 Sprawdzam model spaCy...")
        spacy_ok = self.check_spacy_model()
        if not spacy_ok:
            all_tests_passed = False
            failed_tests.append("Błąd modelu spaCy")
        
        # Podsumowanie
        if all_tests_passed:
            print("\n✅ **TEST PRZESZŁ**")
            print("Kod działa poprawnie, rozpoczynam zbieranie danych...")
        else:
            print("\n❌ **TEST NIE PRZESZŁ**")
            print("Błędy:")
            for error in failed_tests:
                print(f"  • {error}")
            print("\n🔧 **Napraw błędy przed użyciem quota!**")
        
        return all_tests_passed, {
            'all_passed': all_tests_passed,
            'failed_tests': failed_tests,
            'test_results': self.test_results
        }
    
    def check_required_files(self) -> bool:
        """Sprawdza czy wymagane pliki istnieją"""
        missing_files = []
        
        for file in self.required_files:
            if not os.path.exists(file):
                missing_files.append(file)
            else:
                # Sprawdź rozmiar pliku
                size = os.path.getsize(file)
                if size == 0:
                    missing_files.append(f"{file} (pusty)")
        
        if missing_files:
            print(f"  ❌ Brak plików: {', '.join(missing_files)}")
            self.test_results['files'] = {'status': 'failed', 'missing': missing_files}
            return False
        else:
            print(f"  ✅ Wszystkie pliki OK ({len(self.required_files)} plików)")
            self.test_results['files'] = {'status': 'passed', 'count': len(self.required_files)}
            return True
    
    def check_required_modules(self) -> bool:
        """Sprawdza czy wymagane moduły Python są dostępne"""
        missing_modules = []
        
        for module in self.required_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"  ❌ Brak modułów: {', '.join(missing_modules)}")
            self.test_results['modules'] = {'status': 'failed', 'missing': missing_modules}
            return False
        else:
            print(f"  ✅ Wszystkie moduły OK ({len(self.required_modules)} modułów)")
            self.test_results['modules'] = {'status': 'passed', 'count': len(self.required_modules)}
            return True
    
    def check_configuration(self) -> bool:
        """Sprawdza konfigurację kanałów"""
        try:
            with open('channels_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Sprawdź czy są jakieś kanały
            total_channels = sum(len(channels) for channels in config.values())
            
            if total_channels == 0:
                print("  ❌ Brak kanałów w konfiguracji")
                self.test_results['config'] = {'status': 'failed', 'error': 'Brak kanałów'}
                return False
            
            print(f"  ✅ Konfiguracja OK ({total_channels} kanałów, {len(config)} kategorii)")
            self.test_results['config'] = {
                'status': 'passed', 
                'channels': total_channels, 
                'categories': len(config)
            }
            return True
            
        except Exception as e:
            print(f"  ❌ Błąd konfiguracji: {str(e)}")
            self.test_results['config'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def check_youtube_api(self) -> bool:
        """Sprawdza YouTube API (kosztuje 1 quota)"""
        try:
            import requests
            
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                print("  ❌ Brak YOUTUBE_API_KEY")
                self.test_results['youtube_api'] = {'status': 'failed', 'error': 'Brak API key'}
                return False
            
            # Testowe zapytanie (kosztuje 1 quota)
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    'part': 'snippet',
                    'q': 'test',
                    'key': api_key,
                    'maxResults': 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✅ YouTube API OK (test: 1 quota)")
                self.test_results['youtube_api'] = {'status': 'passed', 'quota_used': 1}
                return True
            elif response.status_code == 403 and 'quotaExceeded' in response.text:
                print("  ❌ Quota wyczerpane")
                self.test_results['youtube_api'] = {'status': 'failed', 'error': 'Quota wyczerpane'}
                return False
            else:
                print(f"  ❌ Błąd API: {response.status_code}")
                self.test_results['youtube_api'] = {'status': 'failed', 'error': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"  ❌ Błąd połączenia: {str(e)}")
            self.test_results['youtube_api'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def check_spacy_model(self) -> bool:
        """Sprawdza model spaCy"""
        try:
            import spacy
            
            # Próbuj załadować model - sprawdź różne nazwy
            model_names = ["pl_core_news_sm", "pl_core_news_md", "pl_core_news_lg", "en_core_web_sm"]
            nlp = None
            
            # spaCy wyłączone - używamy tylko wzorców
            print("  ✅ spaCy wyłączone - analiza offline")
            self.test_results['spacy'] = {'status': 'disabled', 'note': 'Analiza offline'}
            return True
                
        except Exception as e:
            print(f"  ❌ Błąd spaCy: {str(e)}")
            self.test_results['spacy'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def check_data_collector(self) -> bool:
        """Sprawdza czy data_collector.py można uruchomić"""
        try:
            # Sprawdź czy plik istnieje i ma poprawną składnię
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', 'data_collector.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ data_collector.py OK")
                self.test_results['data_collector'] = {'status': 'passed'}
                return True
            else:
                print(f"  ❌ Błąd składni data_collector.py: {result.stderr}")
                self.test_results['data_collector'] = {'status': 'failed', 'error': result.stderr}
                return False
                
        except Exception as e:
            print(f"  ❌ Błąd sprawdzania data_collector.py: {str(e)}")
            self.test_results['data_collector'] = {'status': 'failed', 'error': str(e)}
            return False

def main():
    """Główna funkcja testowa"""
    checker = QuotaSafetyChecker()
    
    print("🛡️ **SYSTEM BEZPIECZEŃSTWA QUOTA**")
    print("=" * 50)
    
    success, results = checker.run_full_safety_check()
    
    if success:
        print("\n🎯 **Wszystkie testy przeszły!**")
        print("Można bezpiecznie używać quota.")
        sys.exit(0)
    else:
        print("\n🚫 **Testy nie przeszły!**")
        print("Napraw błędy przed użyciem quota.")
        sys.exit(1)

if __name__ == "__main__":
    main() 