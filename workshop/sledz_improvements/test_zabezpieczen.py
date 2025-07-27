#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TEST ZABEZPIECZEŃ - Test systemu ostrzeżeń quota
==================================================
"""

from sledz_system_v3 import SledzSystemV3

def test_scenarios():
    """Testuje różne scenariusze kosztów"""
    
    sledz = SledzSystemV3()
    
    scenarios = [
        {
            "name": "Tanie @handle linki",
            "message": """
            https://www.youtube.com/@pudelektv
            https://www.youtube.com/@radiozet
            https://www.youtube.com/@Radio_ESKA
            """,
            "expected_cost": 3
        },
        {
            "name": "Mieszane linki - średnie koszty", 
            "message": """
            https://www.youtube.com/@pudelektv
            https://www.youtube.com/watch?v=dQw4w9WgXcQ
            UCShUU9VW-unGNHC-3XMUSmQ
            """,
            "expected_cost": 3  # 1 + 2 + 0
        },
        {
            "name": "DROGIE - linki /c/",
            "message": """
            https://www.youtube.com/c/swiatgwiazd
            https://www.youtube.com/c/radiozet
            """,
            "expected_cost": 200  # 100 + 100
        },
        {
            "name": "Darmowe Channel ID",
            "message": """
            UCShUU9VW-unGNHC-3XMUSmQ
            https://youtube.com/channel/UCvHFbkohgX29NhaUtmkzLmg
            """,
            "expected_cost": 0
        }
    ]
    
    print("🧪 TEST ZABEZPIECZEŃ QUOTA")
    print("=" * 50)
    
    for scenario in scenarios:
        print(f"\n📋 **{scenario['name']}**")
        
        # Analiza kosztów
        analysis = sledz.analyze_links_cost(scenario['message'])
        
        if analysis['success']:
            data = analysis['analysis']
            print(f"   💰 Koszt: {data['total_cost']} quota (oczekiwano: {scenario['expected_cost']})")
            print(f"   📊 Linki: {data['total_links']}")
            print(f"   🎯 Breakdown:")
            print(f"      - Channel ID: {data['channel_ids']} (×0)")
            print(f"      - @handles: {data['handles']} (×1)")
            print(f"      - Filmy: {data['videos']} (×2)")
            print(f"      - Custom /c/: {data['custom_names']} (×100)")
            
            # Test zabezpieczeń
            needs_confirm, reason = sledz.needs_confirmation(data['total_cost'], 9000)  # Symuluj 9000 dostępnego quota
            
            if needs_confirm:
                print(f"   ⚠️ WYMAGA POTWIERDZENIA: {reason}")
            else:
                print(f"   ✅ AUTOMATYCZNE WYKONANIE")
                
        else:
            print(f"   ❌ BŁĄD: {analysis['error']}")
    
    # Test progów
    print(f"\n🎯 **PROGI ZABEZPIECZEŃ:**")
    print(f"   Ostrzeżenie: >{sledz.QUOTA_WARNING_THRESHOLD} quota")
    print(f"   Niebezpieczne: >{sledz.QUOTA_DANGER_THRESHOLD} quota")

if __name__ == "__main__":
    test_scenarios() 