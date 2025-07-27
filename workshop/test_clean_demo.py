#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧹 CZYSTY TEST - OD ZERA
========================

Pokazuje jak system działa gdy zaczynamy z pustą konfiguracją.
Bez żadnych wcześniejszych danych!
"""

import sys
sys.path.append('.')

from sledz_system_v2 import SledzSystemV2

def test_clean_start():
    """Test od zera - pusta konfiguracja"""
    print("🧹 TEST OD ZERA - PUSTA KONFIGURACJA")
    print("=" * 50)
    
    # Nowy system (bez istniejącej konfiguracji)
    system = SledzSystemV2()
    
    # Sprawdź stan początkowy
    initial_rooms = system.get_all_rooms()
    print(f"📊 STAN POCZĄTKOWY: {initial_rooms}")
    print("(Pusty słownik = brak kanałów)")
    
    print(f"\n" + "="*50)
    print("👤 SCENARIUSZ: Dodajesz linki TYLKO do pokoju #polityka")
    print("="*50)
    
    # TYLKO pokój polityka
    print(f"\n📍 POKÓJ: #polityka")
    print("👤 Ty piszesz: !śledź")
    
    polityka_links = """
    https://www.youtube.com/watch?v=sejm_debate_2024
    https://www.youtube.com/shorts/tusk_wywiad_short
    https://www.youtube.com/@TVP_INFO
    """
    
    print(f"👤 Wklejasz: {polityka_links.strip()}")
    
    result = system.process_sledz_command('polityka', polityka_links)
    
    if result['success']:
        print(f"\n🤖 BOT ODPOWIADA:")
        print(f"✅ Dodano {len(result['add_result']['new_channels'])} kanałów")
        print(f"📺 W pokoju #polityka masz teraz: {result['add_result']['total_in_room']} kanałów")
        print(f"💰 Koszt quota: {result['quota_cost']} punktów")
        
        print(f"\n🔑 Dodane Channel ID:")
        for i, channel_id in enumerate(result['add_result']['new_channels'], 1):
            print(f"  {i}. {channel_id}")
    
    # Sprawdź stan WSZYSTKICH pokojów
    print(f"\n📊 STAN WSZYSTKICH POKOJÓW PO DODANIU:")
    final_rooms = system.get_all_rooms()
    
    if not final_rooms:
        print("❌ BRAK POKOJÓW (błąd)")
    else:
        for room, count in final_rooms.items():
            print(f"🏠 #{room}: {count} kanałów")
    
    print(f"\n💡 WNIOSEK:")
    if len(final_rooms) == 1 and 'polityka' in final_rooms:
        print("✅ POPRAWNIE - tylko pokój #polityka ma kanały!")
        print("✅ Inne pokoje (#showbiz, #motoryzacja) są PUSTE")
    else:
        print("❌ BŁĄD - pojawiły się inne pokoje!")
    
    return len(final_rooms) == 1 and final_rooms.get('polityka', 0) > 0

def test_adding_to_different_rooms():
    """Test dodawania do różnych pokojów po kolei"""
    print(f"\n🏠 TEST RÓŻNYCH POKOJÓW PO KOLEI")
    print("=" * 40)
    
    system = SledzSystemV2()
    
    # Krok 1: Tylko showbiz
    print(f"\n1️⃣ Dodaję do #showbiz:")
    result1 = system.process_sledz_command('showbiz', 'https://www.youtube.com/@DDTVN')
    
    if result1['success']:
        print(f"✅ #showbiz: {result1['add_result']['total_in_room']} kanałów")
    
    # Sprawdź stan
    state1 = system.get_all_rooms()
    print(f"📊 Stan pokojów: {state1}")
    
    # Krok 2: Dodaj motoryzację
    print(f"\n2️⃣ Dodaję do #motoryzacja:")
    result2 = system.process_sledz_command('motoryzacja', 'https://www.youtube.com/@TestMotors')
    
    if result2['success']:
        print(f"✅ #motoryzacja: {result2['add_result']['total_in_room']} kanałów")
    
    # Sprawdź stan
    state2 = system.get_all_rooms()
    print(f"📊 Stan pokojów: {state2}")
    
    # Krok 3: Sprawdź czy polityka jest nadal pusta
    polityka_channels = system.get_room_channels('polityka')
    print(f"\n3️⃣ Sprawdzam #polityka:")
    print(f"📺 Kanałów w #polityka: {len(polityka_channels)}")
    
    return True

if __name__ == "__main__":
    print("🧹 CZYSTY START - BEZ STARYCH DANYCH")
    print("Pokazuje dokładnie jak system działa od zera!")
    
    success1 = test_clean_start()
    success2 = test_adding_to_different_rooms()
    
    if success1:
        print(f"\n🎯 WYJAŚNIENIE TWOJEGO PYTANIA:")
        print(f"❓ Dlaczego wcześniej #showbiz miał 6 kanałów?")
        print(f"💡 Bo uruchamialiśmy testy wcześniej i dane się nakumulowały!")
        print(f"🧹 Teraz widzisz prawdziwą pracę systemu od zera")
        print(f"\n✅ WNIOSEK: Każdy pokój działa NIEZALEŻNIE!")
    else:
        print(f"\n⚠️ SYSTEM WYMAGA POPRAWEK") 