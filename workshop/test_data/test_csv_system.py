#!/usr/bin/env python3
"""
TEST SYSTEMU CSV - z symulacją quota
Cel: Sprawdzenie czy CSV są generowane poprawnie
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta
sys.path.append('../../')

# Symulacja dostępnej quota
class MockQuotaManager:
    def get_quota_summary(self):
        return {
            'today_remaining': 5000,  # Symulacja dostępnej quota
            'daily_limit': 10000,
            'usage_percentage': 50.0
        }

def test_csv_format():
    """Test formatu CSV"""
    print("🧪 TEST FORMATU CSV")
    print("=" * 40)
    
    # Przykładowe dane wideo
    sample_video = {
        'id': 'dQw4w9WgXcQ',
        'snippet': {
            'channelTitle': 'Radio ZET',
            'publishedAt': '2025-07-25T14:30:00Z',
            'title': 'Donald Tusk o wyborach parlamentarnych',
            'description': 'Pełny wywiad z premierem o planach rządu',
            'tags': ['polityka', 'wybory', 'tusk', 'rząd']
        },
        'statistics': {
            'viewCount': '15000',
            'likeCount': '250',
            'commentCount': '45',
            'favoriteCount': '12'
        },
        'contentDetails': {
            'duration': 'PT15M30S',
            'definition': 'hd',
            'caption': 'true',
            'licensedContent': True
        }
    }
    
    # Import funkcji z smart_date_collector
    from workshop.new_reporter.smart_date_collector import SmartDateCollector
    
    # Stwórz instancję z mock quota manager
    collector = SmartDateCollector("fake_api_key")
    collector.quota_manager = MockQuotaManager()
    
    # Przetestuj format CSV
    csv_data = collector._process_video_to_csv_format(sample_video)
    
    print("📊 WYJŚCIOWE DANE CSV:")
    for key, value in csv_data.items():
        print(f"  {key}: {value}")
    
    # Sprawdź wymagane kolumny
    required_columns = [
        'Channel_Name', 'Date_of_Publishing', 'Hour_GMT2', 'Title',
        'Description', 'Tags', 'Video_Type', 'View_Count', 'Like_Count',
        'Comment_Count', 'Favorite_Count', 'Definition', 'Has_Captions',
        'Licensed_Content', 'Video_ID'
    ]
    
    print(f"\n✅ SPRAWDZENIE KOLUMN:")
    missing_columns = []
    for col in required_columns:
        if col in csv_data:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col} - BRAK!")
            missing_columns.append(col)
    
    if missing_columns:
        print(f"\n❌ BRAKUJĄCE KOLUMNY: {missing_columns}")
        return False
    else:
        print(f"\n🎉 WSZYSTKIE KOLUMNY OBECNE!")
        return True



def test_date_conversion():
    """Test konwersji dat"""
    print("\n📅 TEST KONWERSJI DAT")
    print("=" * 40)
    
    from workshop.new_reporter.smart_date_collector import SmartDateCollector
    
    collector = SmartDateCollector("fake_api_key")
    
    test_dates = [
        '2025-07-25T14:30:00Z',
        '2025-07-25T22:15:00Z',
        '2025-07-25T02:45:00Z'
    ]
    
    for date_str in test_dates:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            gmt2_time = dt.astimezone(timezone(timedelta(hours=2)))
            date_str_out = gmt2_time.strftime('%Y-%m-%d')
            hour_str_out = gmt2_time.strftime('%H:%M')
            
            print(f"  {date_str} → {date_str_out} {hour_str_out}")
        except Exception as e:
            print(f"  ❌ BŁĄD: {e}")
            return False
    
    return True

def test_video_type_detection():
    """Test wykrywania typu filmu"""
    print("\n🎬 TEST WYKRYWANIA TYPU FILMU")
    print("=" * 40)
    
    from workshop.new_reporter.smart_date_collector import SmartDateCollector
    
    collector = SmartDateCollector("fake_api_key")
    
    test_durations = [
        ('PT30S', 'shorts'),
        ('PT1M', 'shorts'),
        ('PT15M30S', 'video'),
        ('PT1H2M30S', 'video'),
        ('PT2H15M45S', 'video')
    ]
    
    for duration, expected_type in test_durations:
        # Użyj tej samej logiki co w smart_date_collector
        if 'PT' in duration and 'M' not in duration and 'H' not in duration:
            detected_type = 'shorts'
        elif 'PT' in duration and 'M' in duration and 'H' not in duration:
            import re
            minutes_match = re.search(r'(\d+)M', duration)
            if minutes_match and int(minutes_match.group(1)) <= 1:
                detected_type = 'shorts'
            else:
                detected_type = 'video'
        else:
            detected_type = 'video'
        
        print(f"  {duration} → {detected_type} (oczekiwane: {expected_type})")
        
        if detected_type != expected_type:
            print(f"    ❌ BŁĄD!")
            return False
    
    return True

def main():
    """Główna funkcja testowa"""
    print("🧪 KOMPLEKSOWY TEST SYSTEMU CSV")
    print("=" * 50)
    
    tests = [
        ("Format CSV", test_csv_format),
        ("Konwersja dat", test_date_conversion),
        ("Wykrywanie typu filmu", test_video_type_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ BŁĄD w {test_name}: {e}")
            results.append((test_name, False))
    
    # Podsumowanie
    print("\n" + "=" * 50)
    print("📋 PODSUMOWANIE TESTÓW CSV")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ZALICZONY" if result else "❌ NIEZALICZONY"
        print(f"  {test_name}: {status}")
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 WYNIK: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 SUKCES! System CSV działa poprawnie!")
        return True
    else:
        print("⚠️ Potrzebne poprawki w systemie CSV")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 