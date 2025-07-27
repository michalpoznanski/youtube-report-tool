#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TEST ONLY HANDLES - Test systemu akceptującego TYLKO @handle
===============================================================
"""

from sledz_system_v3 import SledzSystemV3

def test_only_handles():
    """Testuje system akceptujący TYLKO @handle"""
    
    sledz = SledzSystemV3()
    
    scenarios = [
        {
            "name": "✅ POPRAWNE @handle linki",
            "message": """
            https://www.youtube.com/@pudelektv
            https://www.youtube.com/@radiozet
            @StanSkupienia.Podcast
            """,
            "should_work": True
        },
        {
            "name": "❌ Channel ID - ODRZUCONE",
            "message": """
            UCShUU9VW-unGNHC-3XMUSmQ
            https://youtube.com/channel/UCvHFbkohgX29NhaUtmkzLmg
            """,
            "should_work": False
        },
        {
            "name": "❌ Linki do filmów - ODRZUCONE",
            "message": """
            https://youtube.com/watch?v=dQw4w9WgXcQ
            https://youtu.be/abc123
            """,
            "should_work": False
        },
        {
            "name": "❌ Linki /c/ - ODRZUCONE",
            "message": """
            https://youtube.com/c/swiatgwiazd
            https://youtube.com/c/radiozet
            """,
            "should_work": False
        },
        {
            "name": "❌ Linki /user/ - ODRZUCONE",
            "message": """
            https://youtube.com/user/starykana
            """,
            "should_work": False
        },
        {
            "name": "❌ MIESZANE - wszystko odrzucone jeśli cokolwiek złe",
            "message": """
            https://www.youtube.com/@pudelektv
            UCShUU9VW-unGNHC-3XMUSmQ
            """,
            "should_work": False
        }
    ]
    
    print("🧪 TEST SYSTEMU TYLKO @HANDLE")
    print("=" * 50)
    
    for scenario in scenarios:
        print(f"\n📋 **{scenario['name']}**")
        
        # Analiza
        analysis = sledz.analyze_links_cost(scenario['message'])
        
        if scenario['should_work']:
            if analysis['success']:
                data = analysis['analysis']
                print(f"   ✅ ZAAKCEPTOWANE")
                print(f"   💰 Koszt: {data['total_cost']} quota")
                print(f"   📊 Poprawnych @handle: {data['valid_handles']}")
            else:
                print(f"   ❌ BŁĄD: {analysis['error']} (oczekiwano sukcesu!)")
        else:
            if not analysis['success']:
                data = analysis['analysis']
                print(f"   ✅ POPRAWNIE ODRZUCONE")
                print(f"   🚫 Błędnych linków: {data['forbidden_links']}")
                print(f"   📝 Pierwszy błąd: {data['errors'][0]['error'] if data['errors'] else 'brak'}")
            else:
                print(f"   ❌ BŁĄD: Zaakceptowano złe linki! (oczekiwano odrzucenia)")

if __name__ == "__main__":
    test_only_handles() 