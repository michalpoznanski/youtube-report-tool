#!/usr/bin/env python3
"""
Test funkcjonalności analizy trendów
Uruchom: python test_trend_analysis.py
"""

import sys
import os
from pathlib import Path

# Dodaj ścieżkę do app
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_trend_store():
    """Test funkcji trend_store"""
    try:
        print("🧪 Testowanie trend_store...")
        
        from trend.core.store.trend_store import (
            auto_analyze_and_save,
            analyze_all_existing_csvs,
            get_latest_analysis
        )
        
        print("✅ Import trend_store udany")
        
        # Test analizy wszystkich CSV
        print("\n🔄 Test analizy wszystkich CSV...")
        result = analyze_all_existing_csvs()
        print(f"Wynik: {result}")
        
        # Test pobierania najnowszej analizy
        print("\n📊 Test pobierania najnowszej analizy...")
        for category in ["PODCAST", "MOTORYZACJA", "POLITYKA"]:
            analysis = get_latest_analysis(category)
            if analysis:
                print(f"✅ {category}: {len(analysis.get('videos', []))} wideo")
            else:
                print(f"⚠️ {category}: Brak danych")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd w test_trend_store: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csv_processor():
    """Test CSVProcessor"""
    try:
        print("\n🧪 Testowanie CSVProcessor...")
        
        from trend.services.csv_processor import CSVProcessor
        
        csv_processor = CSVProcessor()
        print("✅ CSVProcessor utworzony")
        
        # Test dostępnych dat
        for category in ["PODCAST", "MOTORYZACJA", "POLITYKA"]:
            dates = csv_processor.get_available_dates(category)
            print(f"📅 {category}: {len(dates)} dat - {dates[:3] if dates else 'brak'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd w test_csv_processor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dispatcher():
    """Test dispatcher"""
    try:
        print("\n🧪 Testowanie dispatcher...")
        
        from trend.core.dispatcher import analyze_category
        print("✅ Import dispatcher udany")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd w test_dispatcher: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Główna funkcja testowa"""
    print("🚀 Rozpoczynam test funkcjonalności analizy trendów...")
    print("=" * 60)
    
    tests = [
        test_trend_store,
        test_csv_processor,
        test_dispatcher
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"🎯 Testy zakończone: {passed}/{total} ✅")
    
    if passed == total:
        print("🎉 Wszystkie testy przeszły pomyślnie!")
        return 0
    else:
        print("⚠️ Niektóre testy nie przeszły")
        return 1

if __name__ == "__main__":
    exit(main())
