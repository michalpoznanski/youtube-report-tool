#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎭 SYMULACJA DISCORD SCENARIUSZA
===============================

Symuluje dokładnie to co dzieje się gdy użytkownik 
pisze !śledź na różnych pokojach Discord
"""

import sys
sys.path.append('.')

from sledz_system_v2 import SledzSystemV2

def simulate_discord_usage():
    """Symuluje prawdziwe użycie na Discord"""
    print("🎭 SYMULACJA DISCORD - PRAWDZIWY SCENARIUSZ")
    print("=" * 50)
    
    system = SledzSystemV2()
    
    # SCENARIUSZ 1: Pokój #polityka
    print("\n📍 POKÓJ: #polityka")
    print("👤 Ty piszesz: !śledź")
    print("👤 I wklejasz linki:")
    
    polityka_links = """
    https://www.youtube.com/watch?v=sejm_debate_2024
    https://www.youtube.com/shorts/tusk_wywiad_short
    https://www.youtube.com/@TVP_INFO
    https://youtu.be/kaczynski_konferencja
    https://www.youtube.com/channel/UC_PolsatNews_Official
    """
    
    print(f"💬 {polityka_links.strip()}")
    
    result1 = system.process_sledz_command('polityka', polityka_links)
    
    if result1['success']:
        print(f"\n🤖 BOT ODPOWIADA:")
        print(f"✅ Dodano {len(result1['add_result']['new_channels'])} kanałów do pokoju #polityka")
        print(f"📺 Łącznie śledzisz: {result1['add_result']['total_in_room']} kanałów w tym pokoju")
        print(f"💰 Koszt quota: {result1['quota_cost']} punktów")
    
    # SCENARIUSZ 2: Pokój #showbiz  
    print(f"\n📍 POKÓJ: #showbiz")
    print("👤 Ty piszesz: !śledź")
    print("👤 I wklejasz inne linki:")
    
    showbiz_links = """
    https://www.youtube.com/watch?v=gwiazda_wywiad_2024
    https://www.youtube.com/@DDTVN  
    https://youtu.be/festival_relacja
    """
    
    print(f"💬 {showbiz_links.strip()}")
    
    result2 = system.process_sledz_command('showbiz', showbiz_links)
    
    if result2['success']:
        print(f"\n🤖 BOT ODPOWIADA:")
        print(f"✅ Dodano {len(result2['add_result']['new_channels'])} kanałów do pokoju #showbiz")
        print(f"📺 Łącznie śledzisz: {result2['add_result']['total_in_room']} kanałów w tym pokoju")
    
    # SCENARIUSZ 3: Ten sam kanał w różnych pokojach
    print(f"\n📍 POKÓJ: #motoryzacja")  
    print("👤 Ty dodajesz kanał który już jest w polityce:")
    print("💬 https://www.youtube.com/@TVP_INFO")
    
    result3 = system.process_sledz_command('motoryzacja', 'https://www.youtube.com/@TVP_INFO')
    
    if result3['success']:
        cross_room = len(result3['add_result']['cross_room_channels'])
        print(f"\n🤖 BOT ODPOWIADA:")
        print(f"✅ Kanał dodany do #motoryzacja")
        if cross_room > 0:
            print(f"ℹ️ Ten kanał jest już śledzony w innych pokojach: {cross_room}")
    
    # POKAŻ FINALNY STAN
    print(f"\n📊 FINALNY STAN WSZYSTKICH POKOJÓW:")
    all_rooms = system.get_all_rooms()
    for room, count in all_rooms.items():
        channels = system.get_room_channels(room)
        print(f"🏠 #{room}: {count} kanałów")
        for i, channel_id in enumerate(channels[:3], 1):  # Pokaż pierwsze 3
            print(f"   {i}. {channel_id}")
        if count > 3:
            print(f"   ... i {count-3} więcej")
    
    return len(all_rooms) >= 3

def test_what_happens_next():
    """Test co dzieje się po dodaniu kanałów"""
    print(f"\n🔄 CO DZIEJE SIĘ DALEJ:")
    print("=" * 30)
    
    system = SledzSystemV2()
    
    # Symuluj że mamy kanały w pokoju
    print("📍 Na pokoju #polityka masz teraz kanały")
    polityka_channels = system.get_room_channels('polityka')
    print(f"📺 Kanałów do śledzenia: {len(polityka_channels)}")
    
    print(f"\n🎯 NASTĘPNE KROKI:")
    print(f"1️⃣ Piszesz: !raport")
    print(f"   📊 Bot zbiera dane z {len(polityka_channels)} kanałów")
    print(f"   📁 Tworzy plik CSV z filmami z ostatnich 7 dni")
    
    print(f"\n2️⃣ Piszesz: !name") 
    print(f"   🔍 Bot analizuje CSV")
    print(f"   🏷️ Wyciąga nazwiska z tytułów")
    print(f"   📈 Pokazuje statystyki (kto najczęściej)")
    
    return True

if __name__ == "__main__":
    print("🎭 TEST SCENARIUSZA Z DISCORD")
    print("Dokładnie to samo co będzie działo się na bocie!")
    
    success1 = simulate_discord_usage()
    success2 = test_what_happens_next()
    
    if success1 and success2:
        print(f"\n🚀 SCENARIUSZ DZIAŁA PERFEKCYJNIE!")
        print(f"\n💡 PODSUMOWANIE:")
        print(f"• Wklejasz linki na dowolnym pokoju")
        print(f"• !śledź automatycznie dodaje kanały do tego pokoju") 
        print(f"• !raport zbiera dane tylko z kanałów tego pokoju")
        print(f"• !name analizuje zebrane dane")
        print(f"\n🎯 Każdy pokój Discord = oddzielna baza kanałów!")
    else:
        print(f"\n⚠️ SCENARIUSZ WYMAGA POPRAWEK") 