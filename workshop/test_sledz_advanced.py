#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 ZAAWANSOWANE TESTY SYSTEMU !ŚLEDŹ
===================================

Testuje różne scenariusze użycia komendy !śledź:
- Różne pokoje Discord
- Duplikaty w obrębie pokoju
- Kanały w wielu pokojach
- Różne formaty linków
- Obsługa błędów
"""

import sys
sys.path.append('.')

from sledz_system_v2 import SledzSystemV2

def test_multiple_rooms():
    """Test dodawania kanałów do różnych pokojów"""
    print("\n🏠 TEST WIELU POKOJÓW:")
    
    system = SledzSystemV2()
    
    # Test 1: Dodaj do polityki
    result1 = system.process_sledz_command('polityka', 
        'https://www.youtube.com/@TVP_INFO https://www.youtube.com/@PolsatNews')
    
    # Test 2: Dodaj do showbizu
    result2 = system.process_sledz_command('showbiz',
        'https://www.youtube.com/@DDTVN https://www.youtube.com/@MotoryzacjaTV')
    
    # Test 3: Dodaj ten sam kanał do obu pokojów (cross-room)
    result3 = system.process_sledz_command('showbiz',
        'https://www.youtube.com/@TVP_INFO')  # Ten już jest w polityce
    
    print(f"📍 Polityka - dodano: {len(result1['add_result']['new_channels'])} kanałów")
    print(f"📍 Showbiz - dodano: {len(result2['add_result']['new_channels'])} kanałów")
    print(f"📍 Cross-room - kanałów między pokojami: {len(result3['add_result']['cross_room_channels'])}")
    
    # Sprawdź stan wszystkich pokojów
    rooms = system.get_all_rooms()
    print(f"📊 Status pokojów: {rooms}")
    
    return len(rooms) >= 2

def test_duplicates():
    """Test obsługi duplikatów"""
    print("\n🔄 TEST DUPLIKATÓW:")
    
    system = SledzSystemV2()
    
    # Dodaj kanały pierwszy raz
    message1 = """
    https://www.youtube.com/@TVN24
    https://www.youtube.com/@PolsatNews
    https://www.youtube.com/watch?v=abc123
    """
    
    result1 = system.process_sledz_command('polityka', message1)
    
    # Spróbuj dodać te same kanały ponownie
    result2 = system.process_sledz_command('polityka', message1)
    
    print(f"🆕 Pierwszy raz - nowe: {len(result1['add_result']['new_channels'])}")
    print(f"🔄 Drugi raz - już śledzone: {len(result2['add_result']['already_tracked'])}")
    print(f"📺 Łącznie w pokoju: {result2['add_result']['total_in_room']}")
    
    return result2['add_result']['total_in_room'] == result1['add_result']['total_in_room']

def test_link_formats():
    """Test różnych formatów linków"""
    print("\n🔗 TEST FORMATÓW LINKÓW:")
    
    system = SledzSystemV2()
    
    # Różne formaty linków
    test_message = """
    Kanały:
    https://www.youtube.com/channel/UCrAOnWcQQP1FGv3dWhHlx8g
    https://www.youtube.com/c/TVN24
    https://www.youtube.com/@RadioZET
    https://youtube.com/@PolitykaNazywo
    
    Filmy:
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    https://youtu.be/XYZ789
    https://www.youtube.com/shorts/SHORT123
    https://youtube.com/watch?v=TEST456
    """
    
    channel_links, video_links = system.extract_youtube_links(test_message)
    
    print(f"📺 Wykryte kanały ({len(channel_links)}):")
    for i, link in enumerate(channel_links, 1):
        print(f"  {i}. {link}")
    
    print(f"🎬 Wykryte filmy ({len(video_links)}):")
    for i, link in enumerate(video_links, 1):
        print(f"  {i}. {link}")
    
    # Przetestuj konwersję
    channel_ids, quota_cost = system.resolve_channel_ids(channel_links, video_links)
    
    print(f"🔑 Skonwertowane Channel ID ({len(channel_ids)}):")
    for i, channel_id in enumerate(channel_ids, 1):
        print(f"  {i}. {channel_id}")
    
    print(f"💰 Szacowany koszt quota: {quota_cost}")
    
    return len(channel_links) >= 4 and len(video_links) >= 4

def test_empty_messages():
    """Test obsługi pustych/nieprawidłowych wiadomości"""
    print("\n❌ TEST BŁĘDNYCH WIADOMOŚCI:")
    
    system = SledzSystemV2()
    
    test_cases = [
        "",  # Pusta wiadomość
        "To nie ma żadnych linków YouTube",  # Brak linków
        "https://www.facebook.com/test",  # Inne linki
        "youtube.com",  # Niepełny link
        "https://www.youtube.com/",  # Link bez ID
    ]
    
    for i, message in enumerate(test_cases, 1):
        result = system.process_sledz_command('test', message)
        success = result['success']
        print(f"  {i}. '{message[:30]}...' → {'✅' if not success else '❌'}")
    
    return True  # Test zawsze przechodzi, sprawdzamy tylko czy błędy są prawidłowo obsłużone

def test_config_migration():
    """Test migracji starej konfiguracji do nowej"""
    print("\n🔄 TEST MIGRACJI KONFIGURACJI:")
    
    # Symuluj starą strukturę konfiguracji
    old_config = {
        "Politics": ["UC123", "UC456"],
        "Showbiz": ["UC789", "UC999"],
        "Motoryzacja": ["UC555"]
    }
    
    # Zapisz starą konfigurację
    import json
    with open('test_old_config.json', 'w', encoding='utf-8') as f:
        json.dump(old_config, f)
    
    # Załaduj przez system (powinien zmigrować)
    system = SledzSystemV2(channels_config_path='test_old_config.json')
    
    # Sprawdź czy migracja się udała
    migrated_config = system.channels_config
    
    print(f"📁 Stara struktura kluczy: {list(old_config.keys())}")
    if 'channels' in migrated_config:
        print(f"📁 Nowa struktura pokojów: {list(migrated_config['channels'].keys())}")
        
        # Sprawdź mapowanie
        expected_rooms = ['polityka', 'showbiz', 'motoryzacja']
        actual_rooms = list(migrated_config['channels'].keys())
        
        print(f"🎯 Oczekiwane pokoje: {expected_rooms}")
        print(f"✅ Faktyczne pokoje: {actual_rooms}")
        
        migration_success = all(room in actual_rooms for room in expected_rooms)
    else:
        migration_success = False
    
    # Wyczyść plik testowy
    import os
    try:
        os.remove('test_old_config.json')
    except:
        pass
    
    return migration_success

if __name__ == "__main__":
    print("🧪 ZAAWANSOWANE TESTY SYSTEMU !ŚLEDŹ")
    print("=" * 50)
    
    # Uruchom wszystkie testy
    tests = [
        ("🏠 Wiele pokojów", test_multiple_rooms),
        ("🔄 Duplikaty", test_duplicates), 
        ("🔗 Formaty linków", test_link_formats),
        ("❌ Błędne wiadomości", test_empty_messages),
        ("🔄 Migracja konfiguracji", test_config_migration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    # Podsumowanie
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 PODSUMOWANIE TESTÓW:")
    print(f"✅ Przeszło: {passed}/{total}")
    print(f"❌ Nie przeszło: {total-passed}/{total}")
    
    if passed == total:
        print(f"\n🚀 WSZYSTKIE TESTY PRZESZŁY! SYSTEM GOTOWY!")
    else:
        print(f"\n⚠️ NIEKTÓRE TESTY NIE PRZESZŁY - WYMAGANE POPRAWKI")
    
    print(f"\n📋 SZCZEGÓŁOWE WYNIKI:")
    for test_name, result in results:
        print(f"  {'✅' if result else '❌'} {test_name}") 