#!/usr/bin/env python3
"""
TEST AUTOMATYCZNEJ SYNCHRONIZACJI Z GITHUB TOKEN
===============================================

Testuje Railway Sync V2 z prawdziwym GitHub tokenem
"""

from railway_sync_v2 import RailwaySyncV2
from datetime import datetime

# Twój GitHub token
# 🛡️ BEZPIECZEŃSTWO: Token usunięty!
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("❌ Brak GITHUB_TOKEN w zmiennych środowiskowych!")

def test_token_sync():
    """Testuje automatyczną synchronizację z tokenem"""
    
    print("🧪 TEST AUTOMATYCZNEJ SYNCHRONIZACJI")
    print("=" * 50)
    
    try:
        # Inicjalizuj z tokenem
        print("🔑 Inicjalizuję Railway Sync V2 z tokenem...")
        sync = RailwaySyncV2(github_token=GITHUB_TOKEN)
        
        # Test setup git repo
        print("\n📦 Testuję setup git repo...")
        if sync.setup_local_git():
            print("✅ Git repo sklonowane pomyślnie!")
        else:
            print("❌ Problem z setup git repo")
            return False
        
        # Test automatycznej synchronizacji
        print("\n🚀 Testuję automatyczną synchronizację...")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Test auto sync - {timestamp}"
        
        if sync.sync_to_railway_auto(commit_message=commit_msg):
            print("✅ Automatyczna synchronizacja zakończona!")
            print("🚂 Railway powinien automatycznie wykryć zmiany")
            return True
        else:
            print("❌ Problem z automatyczną synchronizacją")
            return False
            
    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        return False

def test_quick_sync():
    """Testuje szybką synchronizację jednego pliku"""
    
    print("\n⚡ TEST SZYBKIEJ SYNCHRONIZACJI")
    print("=" * 40)
    
    try:
        sync = RailwaySyncV2(github_token=GITHUB_TOKEN)
        
        # Test quick sync main.py
        print("📄 Testuję quick sync main.py...")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Quick test sync - {timestamp}"
        
        if sync.quick_sync("main.py", commit_msg):
            print("✅ Quick sync zakończony!")
            return True
        else:
            print("❌ Problem z quick sync")
            return False
            
    except Exception as e:
        print(f"❌ Błąd podczas quick sync: {e}")
        return False

if __name__ == "__main__":
    print("🎯 RAILWAY SYNC V2 - TEST Z TOKENEM")
    print("=" * 50)
    
    # Test 1: Pełna synchronizacja
    success1 = test_token_sync()
    
    # Test 2: Quick sync
    success2 = test_quick_sync()
    
    print("\n📊 WYNIKI TESTÓW:")
    print(f"✅ Pełna sync: {'SUKCES' if success1 else 'BŁĄD'}")
    print(f"✅ Quick sync: {'SUKCES' if success2 else 'BŁĄD'}")
    
    if success1 and success2:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("🚀 Railway Sync V2 gotowy do użycia!")
    else:
        print("\n⚠️ NIEKTÓRE TESTY NIE PRZESZŁY")
        print("🔧 Sprawdź błędy powyżej") 