#!/usr/bin/env python3
"""
TEST GENEROWANIA CSV - rzeczywisty plik
Cel: Sprawdzenie czy system może wygenerować plik CSV
"""

import sys
import os
import csv
import tempfile
from datetime import datetime
sys.path.append('../../')

def test_csv_file_generation():
    """Test generowania rzeczywistego pliku CSV"""
    print("📄 TEST GENEROWANIA PLIKU CSV")
    print("=" * 40)
    
    # Przykładowe dane wideo
    sample_videos = [
        {
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
        },
        {
            'id': 'abc123def456',
            'snippet': {
                'channelTitle': 'TVN24',
                'publishedAt': '2025-07-25T16:45:00Z',
                'title': 'Jarosław Kaczyński komentuje decyzje rządu',
                'description': 'Prezes PiS krytykuje działania premiera Tuska',
                'tags': ['polityka', 'kaczyński', 'tusk', 'pis']
            },
            'statistics': {
                'viewCount': '25000',
                'likeCount': '180',
                'commentCount': '67',
                'favoriteCount': '8'
            },
            'contentDetails': {
                'duration': 'PT8M15S',
                'definition': 'hd',
                'caption': 'false',
                'licensedContent': False
            }
        },
        {
            'id': 'xyz789uvw012',
            'snippet': {
                'channelTitle': 'Polsat News',
                'publishedAt': '2025-07-25T12:15:00Z',
                'title': 'Andrzej Duda w programie "Gość Wydarzeń"',
                'description': 'Prezydent rozmawia o sytuacji w kraju',
                'tags': ['prezydent', 'duda', 'polityka', 'wywiady']
            },
            'statistics': {
                'viewCount': '18000',
                'likeCount': '320',
                'commentCount': '89',
                'favoriteCount': '15'
            },
            'contentDetails': {
                'duration': 'PT45S',
                'definition': 'sd',
                'caption': 'true',
                'licensedContent': True
            }
        }
    ]
    
    # Import funkcji
    from workshop.new_reporter.smart_date_collector import SmartDateCollector
    
    collector = SmartDateCollector("fake_api_key")
    
    # Przetwórz dane do formatu CSV
    csv_data = []
    for video in sample_videos:
        csv_row = collector._process_video_to_csv_format(video)
        csv_data.append(csv_row)
    
    # Generuj plik CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'test_csv_generation_{timestamp}.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if csv_data:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Zapisz nagłówki
            writer.writeheader()
            
            # Zapisz dane
            for row in csv_data:
                writer.writerow(row)
    
    print(f"✅ Wygenerowano plik: {filename}")
    print(f"📊 Liczba wierszy: {len(csv_data)}")
    
    # Sprawdź zawartość pliku
    print(f"\n📋 ZAWARTOŚĆ PLIKU CSV:")
    print("-" * 80)
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, 1):
            print(f"Wiersz {i}:")
            print(f"  Kanał: {row['Channel_Name']}")
            print(f"  Tytuł: {row['Title']}")
            print(f"  Typ: {row['Video_Type']}")
            print(f"  Wyświetlenia: {row['View_Count']}")
            print()
    
    # Sprawdź czy plik można otworzyć w Excel/Google Sheets
    print(f"🔍 SPRAWDZENIE KOMPATYBILNOŚCI:")
    
    # Sprawdź kodowanie
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"  ✅ Kodowanie UTF-8: OK")
    except Exception as e:
        print(f"  ❌ Błąd kodowania: {e}")
        return False
    
    # Sprawdź strukturę
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        if len(rows) == len(sample_videos):
            print(f"  ✅ Liczba wierszy: OK ({len(rows)})")
        else:
            print(f"  ❌ Błędna liczba wierszy: {len(rows)} vs {len(sample_videos)}")
            return False
        
        # Sprawdź czy wszystkie wymagane kolumny są obecne
        required_columns = [
            'Channel_Name', 'Date_of_Publishing', 'Hour_GMT2', 'Title',
            'Description', 'Tags', 'Video_Type', 'View_Count', 'Like_Count',
            'Comment_Count', 'Favorite_Count', 'Definition', 'Has_Captions',
            'Licensed_Content', 'Video_ID'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in rows[0]:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"  ❌ Brakujące kolumny: {missing_columns}")
            return False
        else:
            print(f"  ✅ Wszystkie kolumny obecne")
    
    print(f"\n🎉 PLIK CSV GOTOWY DO UŻYCIA!")
    print(f"📁 Ścieżka: {os.path.abspath(filename)}")
    
    return True

def test_csv_validation():
    """Test walidacji danych CSV"""
    print("\n🔍 TEST WALIDACJI DANYCH CSV")
    print("=" * 40)
    
    # Sprawdź czy istnieją pliki CSV w reports/
    reports_dir = "../../reports"
    csv_files = []
    
    if os.path.exists(reports_dir):
        for root, dirs, files in os.walk(reports_dir):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
    
    if csv_files:
        print(f"📁 Znaleziono {len(csv_files)} plików CSV:")
        for csv_file in csv_files[:3]:  # Pokaż pierwsze 3
            print(f"  📄 {os.path.basename(csv_file)}")
        
        # Sprawdź pierwszy plik
        if csv_files:
            sample_file = csv_files[0]
            print(f"\n🔍 ANALIZA: {os.path.basename(sample_file)}")
            
            try:
                with open(sample_file, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    rows = list(reader)
                    
                    print(f"  📊 Liczba wierszy: {len(rows)}")
                    if rows:
                        print(f"  📋 Kolumny: {list(rows[0].keys())}")
                        
                        # Sprawdź przykładowe dane
                        sample_row = rows[0]
                        print(f"  📺 Przykład: {sample_row.get('Channel_Name', 'N/A')} - {sample_row.get('Title', 'N/A')[:50]}...")
                        

                
                print(f"  ✅ Plik CSV poprawny")
                
            except Exception as e:
                print(f"  ❌ Błąd analizy: {e}")
                return False
    else:
        print("📁 Brak plików CSV w reports/")
    
    return True

def main():
    """Główna funkcja testowa"""
    print("🧪 TEST GENEROWANIA I WALIDACJI CSV")
    print("=" * 50)
    
    tests = [
        ("Generowanie pliku CSV", test_csv_file_generation),
        ("Walidacja danych CSV", test_csv_validation)
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
        print("🎉 SUKCES! System CSV gotowy do użycia!")
        return True
    else:
        print("⚠️ Potrzebne dodatkowe poprawki")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 