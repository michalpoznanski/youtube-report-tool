#!/usr/bin/env python3
"""
Test trwałości danych po restarcie
"""

import json
import tempfile
from pathlib import Path
from app.storage.state_manager import StateManager

def test_data_persistence():
    """Testuje trwałość danych"""
    print("🧪 Test trwałości danych:")
    print("=" * 50)
    
    # Utwórz tymczasowy katalog dla testów
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Używam katalogu testowego: {temp_dir}")
        
        # Inicjalizuj StateManager z katalogiem testowym
        state_manager = StateManager(temp_dir)
        
        # Dodaj testowe dane
        print("\n📝 Dodawanie testowych danych...")
        
        # Dodaj kanał
        test_channel = {
            'id': 'UC123456789',
            'title': 'Test Channel',
            'description': 'Test description',
            'subscriber_count': 1000,
            'video_count': 50,
            'view_count': 100000,
            'thumbnail': 'https://example.com/thumb.jpg',
            'published_at': '2020-01-01T00:00:00Z'
        }
        state_manager.add_channel(test_channel, 'test_category')
        
        # Dodaj quota
        state_manager.add_quota_used(150)
        
        # Sprawdź czy dane zostały zapisane
        print("\n📊 Sprawdzanie zapisanych danych...")
        
        # Sprawdź pliki
        channels_file = Path(temp_dir) / "channels.json"
        quota_file = Path(temp_dir) / "quota_state.json"
        system_file = Path(temp_dir) / "system_state.json"
        
        print(f"📄 channels.json istnieje: {channels_file.exists()}")
        print(f"📄 quota_state.json istnieje: {quota_file.exists()}")
        print(f"📄 system_state.json istnieje: {system_file.exists()}")
        
        # Sprawdź zawartość plików
        if channels_file.exists():
            with open(channels_file, 'r') as f:
                channels_data = json.load(f)
            print(f"📺 Kanały w pliku: {channels_data}")
        
        if quota_file.exists():
            with open(quota_file, 'r') as f:
                quota_data = json.load(f)
            print(f"📊 Quota w pliku: {quota_data}")
        
        # Utwórz nowy StateManager (symulacja restartu)
        print("\n🔄 Symulacja restartu - tworzenie nowego StateManager...")
        new_state_manager = StateManager(temp_dir)
        
        # Sprawdź czy dane zostały wczytane
        print("\n📊 Sprawdzanie wczytanych danych po restarcie...")
        
        channels = new_state_manager.get_channels()
        quota_state = new_state_manager.get_quota_state()
        system_state = new_state_manager.get_system_state()
        
        print(f"📺 Kanały po restarcie: {channels}")
        print(f"📊 Quota po restarcie: {quota_state}")
        print(f"⚙️ System po restarcie: {system_state}")
        
        # Sprawdź czy dane są identyczne
        channels_count = sum(len(channels) for channels in channels.values())
        quota_used = quota_state.get('used', 0)
        
        print(f"\n📈 Podsumowanie:")
        print(f"   Kanały: {channels_count}")
        print(f"   Quota użyte: {quota_used}")
        
        if channels_count > 0 and quota_used > 0:
            print("✅ Test trwałości danych: SUKCES")
        else:
            print("❌ Test trwałości danych: BŁĄD")

if __name__ == "__main__":
    test_data_persistence() 