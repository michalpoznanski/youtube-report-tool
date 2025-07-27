#!/usr/bin/env python3
"""
SCENARIUSZE TESTOWE dla QuotaSafeCollector
Cel: 95% pewności przed wyjściem z warsztatu
"""

import sys
import os
sys.path.append('../../')
from workshop.new_reporter.quota_safe_collector import QuotaSafeCollector

def run_comprehensive_tests():
    """Kompleksowe testy wszystkich scenariuszy"""
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Brak YOUTUBE_API_KEY")
        return False
    
    collector = QuotaSafeCollector(api_key)
    
    print("🧪 KOMPLEKSOWE TESTY QUOTA-SAFE COLLECTOR")
    print("=" * 50)
    
    # SCENARIUSZ 1: Małe kanały (bezpieczne)
    print("\n📍 SCENARIUSZ 1: Małe kanały (3 kanały)")
    small_channels = [
        "UC-wh71MEZ4KAx94aZyoG_qg",  # Channel ID
        "UCvHFbkohgX29NhaUtmkzLmg",  # Channel ID
        "radiozet"                   # Handle
    ]
    test_scenario_1 = run_scenario_test(collector, small_channels, "MAŁE_KANAŁY")
    
    # SCENARIUSZ 2: Średnie kanały (10 kanałów - limit)
    print("\n📍 SCENARIUSZ 2: Średnie kanały (10 kanałów - limit)")
    medium_channels = [
        "UC-wh71MEZ4KAx94aZyoG_qg", "UCvHFbkohgX29NhaUtmkzLmg", 
        "UC3R8278fJUWn2ysrOCJrmAQ", "UCmuaurR3Fl5ugr6Bi066tHA",
        "radiozet", "RMF24Video", "UC_vMDcmkuEvw0N-gaP35wTA",
        "UCgL0f77U3iEPSSU-Mv5yV5g", "UCU8ueU3NrJdum0m94TJSdkw",
        "UCkC9YgH_FlqOhOIoTDFt4CA"
    ]
    test_scenario_2 = run_scenario_test(collector, medium_channels, "ŚREDNIE_KANAŁY")
    
    # SCENARIUSZ 3: Duże kanały (20 kanałów - przekroczenie)
    print("\n📍 SCENARIUSZ 3: Duże kanały (20 kanałów - za dużo)")
    large_channels = medium_channels + [
        "ORB_NEWS", "UCgPtAPMjueWjDUG25imAt_A", "RynekKrowoderski",
        "UC0DpwRtGw4K9tNLnUJqx9qA", "goniecredakcja", "UCW5bKAEBFWz1yHKUEw3VLFg",
        "UCpchzx2u5Ab8YASeJsR1WIw", "polsatnewsplofc", "UCb7O4-iI4pEO5UZPlOBr0Ug",
        "UCZ9dViYsOulUhR04hVkpsMw"
    ]
    test_scenario_3 = run_scenario_test(collector, large_channels, "DUŻE_KANAŁY")
    
    # SCENARIUSZ 4: Tylko handles (problematyczne)
    print("\n📍 SCENARIUSZ 4: Tylko handles (wyższa quota)")
    handle_channels = [
        "radiozet", "RMF24Video", "ORB_NEWS", "RynekKrowoderski",
        "goniecredakcja", "polsatnewsplofc", "OKOpress", "wp-pl"
    ]
    test_scenario_4 = run_scenario_test(collector, handle_channels, "TYLKO_HANDLES")
    
    # SCENARIUSZ 5: Mix ID + handles
    print("\n📍 SCENARIUSZ 5: Mix Channel IDs + Handles")
    mixed_channels = [
        "UC-wh71MEZ4KAx94aZyoG_qg", "UCvHFbkohgX29NhaUtmkzLmg",  # IDs
        "radiozet", "RMF24Video",  # Handles
        "UC3R8278fJUWn2ysrOCJrmAQ", "UCmuaurR3Fl5ugr6Bi066tHA",  # IDs
        "ORB_NEWS", "goniecredakcja"  # Handles
    ]
    test_scenario_5 = run_scenario_test(collector, mixed_channels, "MIX_ID_HANDLES")
    
    # SCENARIUSZ 6: Różne okresy czasu
    print("\n📍 SCENARIUSZ 6: Różne okresy czasu")
    test_time_periods(collector, small_channels)
    
    # SCENARIUSZ 7: Filtrowanie bezpieczeństwa
    print("\n📍 SCENARIUSZ 7: Automatyczne filtrowanie kanałów")
    test_safety_filtering(collector, large_channels)
    
    # PODSUMOWANIE
    print("\n" + "=" * 50)
    print("📋 PODSUMOWANIE TESTÓW")
    print("=" * 50)
    
    scenarios = [test_scenario_1, test_scenario_2, test_scenario_3, test_scenario_4, test_scenario_5]
    passed = sum(1 for s in scenarios if s)
    total = len(scenarios)
    
    success_rate = (passed / total) * 100
    print(f"✅ Zaliczone scenariusze: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 SUKCES! Gotowy do wyjścia z warsztatu!")
        return True
    else:
        print("⚠️ Potrzebne dodatkowe poprawki")
        return False

def run_scenario_test(collector, channels, scenario_name):
    """Uruchamia test pojedynczego scenariusza"""
    try:
        # Test szacowania kosztów
        cost_estimate = collector.estimate_collection_cost(channels, 7)
        
        # Test bezpieczeństwa
        safety_check = collector.can_collect_safely(channels, 7)
        
        # Test dry run
        dry_run = collector.collect_data_safely(channels, 7, dry_run=True)
        
        print(f"💰 Koszt: {cost_estimate['costs']['total']} quota")
        print(f"🎯 {cost_estimate['recommendation']}")
        print(f"🛡️ Bezpieczne: {'✅' if safety_check['safe'] else '❌'}")
        print(f"🧪 Dry run: {'✅' if dry_run.get('success') else '❌'}")
        
        # Ocena scenariusza
        if cost_estimate['costs']['total'] < 1000 and dry_run.get('success'):
            print(f"✅ {scenario_name}: ZALICZONY")
            return True
        else:
            print(f"❌ {scenario_name}: NIEZALICZONY")
            return False
            
    except Exception as e:
        print(f"❌ {scenario_name}: BŁĄD - {str(e)}")
        return False

def test_time_periods(collector, channels):
    """Test różnych okresów czasu"""
    periods = [1, 3, 7, 14, 30]
    
    for days in periods:
        cost = collector.estimate_collection_cost(channels, days)
        print(f"📅 {days} dni: {cost['costs']['total']} quota - {cost['recommendation']}")

def test_safety_filtering(collector, large_channels):
    """Test automatycznego filtrowania kanałów"""
    filtered = collector.filter_channels_by_safety(large_channels, max_cost=500)
    
    print(f"🔒 Bezpieczne kanały: {len(filtered['safe_channels'])}")
    print(f"🚫 Odrzucone kanały: {len(filtered['dropped_channels'])}")
    print(f"💰 Szacowany koszt: {filtered['estimated_cost']} quota")

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1) 