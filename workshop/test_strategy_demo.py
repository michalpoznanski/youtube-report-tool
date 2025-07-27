#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 DEMO NOWEJ STRATEGII
======================

Pokazuje jak działa workflow:
!śledź → !raport → !name

Scenariusz:
1. Użytkownik na pokoju "polityka" wkleja różne linki YT
2. !śledź automatycznie znajduje kanały i dodaje do pokoju
3. !raport zbiera dane z tych kanałów
4. !name analizuje zebrane dane
"""

import sys
sys.path.append('.')

from sledz_system_v2 import SledzSystemV2

def demo_sledz_strategy():
    """Demo nowej strategii !śledź"""
    print("🎯 DEMO NOWEJ STRATEGII !ŚLEDŹ")
    print("=" * 50)
    
    # Inicjalizuj system
    system = SledzSystemV2()
    
    # SCENARIUSZ: Użytkownik na pokoju "polityka" wkleja różne linki
    print("\n📍 POKÓJ: polityka")
    print("👤 UŻYTKOWNIK wkleja wiadomość:")
    
    user_message = """
    Hej, znalazłem ciekawe materiały:
    
    https://www.youtube.com/watch?v=ABC123_polityka_film
    https://www.youtube.com/shorts/DEF456_news_short  
    https://www.youtube.com/@TVNWarszawa
    https://www.youtube.com/channel/UC_PolitykaNazywo_ID
    https://youtu.be/GHI789_debate_video
    """
    
    print(f"💬 '{user_message.strip()}'")
    
    # KROK 1: !śledź automatycznie przetwarza
    print(f"\n🤖 SYSTEM !ŚLEDŹ PRZETWARZA:")
    result = system.process_sledz_command('polityka', user_message)
    
    if result['success']:
        print(f"✅ Sukces!")
        print(f"📊 Znalezione linki:")
        print(f"  📺 Kanały: {result['found_links']['channels']}")
        print(f"  🎬 Filmy: {result['found_links']['videos']} (→ Channel ID)")
        print(f"  📋 Łącznie: {result['found_links']['total']}")
        
        print(f"\n🔄 Rezultat:")
        print(f"  🆕 Nowe kanały w pokoju: {len(result['add_result']['new_channels'])}")
        print(f"  📺 Łącznie kanałów w 'polityka': {result['add_result']['total_in_room']}")
        
        print(f"\n🔑 Dodane Channel ID:")
        for i, channel_id in enumerate(result['add_result']['new_channels'], 1):
            print(f"  {i}. {channel_id}")
    else:
        print(f"❌ Błąd: {result['error']}")
        return False
    
    # KROK 2: Pokaż jak !raport będzie używał tych kanałów
    print(f"\n📊 NASTĘPNY KROK - !RAPORT:")
    room_channels = system.get_room_channels('polityka')
    print(f"🎯 !raport na pokoju 'polityka' będzie śledzić {len(room_channels)} kanałów:")
    for i, channel_id in enumerate(room_channels, 1):
        print(f"  {i}. {channel_id}")
    
    # KROK 3: Pokaż strategię !name
    print(f"\n🔍 NASTĘPNY KROK - !NAME:")
    print(f"📝 !name przeanalizuje dane CSV z !raport i:")
    print(f"  🏷️ Wyciągnie nazwiska z tytułów filmów")
    print(f"  🔄 Znormalizuje polskie imiona (Tuskiem → Tusk)")
    print(f"  🎯 Przesegreguje treści (polityka vs showbiz)")
    
    return True

def demo_multiple_rooms():
    """Demo dodawania do różnych pokojów"""
    print(f"\n🏠 DEMO RÓŻNYCH POKOJÓW:")
    print("=" * 30)
    
    system = SledzSystemV2()
    
    scenarios = [
        ('polityka', 'https://www.youtube.com/watch?v=sejm_debate_2024'),
        ('showbiz', 'https://www.youtube.com/watch?v=celebryta_wywiad'),
        ('motoryzacja', 'https://www.youtube.com/@TestMotors'),
    ]
    
    for room, link in scenarios:
        result = system.process_sledz_command(room, link)
        if result['success']:
            new_count = len(result['add_result']['new_channels'])
            total_count = result['add_result']['total_in_room']
            print(f"📍 {room}: +{new_count} kanał → łącznie {total_count}")
        else:
            print(f"❌ {room}: błąd")
    
    # Pokaż finalny stan
    all_rooms = system.get_all_rooms()
    print(f"\n📊 FINALNY STAN POKOJÓW:")
    for room, count in all_rooms.items():
        print(f"  🏠 {room}: {count} kanałów")
    
    return len(all_rooms) >= 3

if __name__ == "__main__":
    # Uruchom demo
    success1 = demo_sledz_strategy()
    success2 = demo_multiple_rooms()
    
    print(f"\n🎯 PODSUMOWANIE STRATEGII:")
    print(f"✅ Główne demo: {'SUKCES' if success1 else 'BŁĄD'}")
    print(f"✅ Wiele pokojów: {'SUKCES' if success2 else 'BŁĄD'}")
    
    if success1 and success2:
        print(f"\n🚀 STRATEGIA DZIAŁA IDEALNIE!")
        print(f"📋 WORKFLOW:")
        print(f"  1️⃣ !śledź → automatycznie dodaje kanały z linków")
        print(f"  2️⃣ !raport → zbiera surowe dane z śledzonych kanałów") 
        print(f"  3️⃣ !name → analizuje i segreguje dane")
        print(f"\n💡 FILOZOFIA: Każda komenda ma jasną, pojedynczą odpowiedzialność!")
    else:
        print(f"\n⚠️ STRATEGIA WYMAGA POPRAWEK") 