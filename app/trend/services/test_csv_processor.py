"""
Test dla CSVProcessor - sprawdza działanie serwisu przetwarzania CSV
"""

import sys
from pathlib import Path
from datetime import date

# Dodaj ścieżkę do modułu app
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.trend.services.csv_processor import CSVProcessor, get_trend_data

def test_csv_processor():
    """Test podstawowej funkcjonalności CSVProcessor"""
    
    print("🧪 Testowanie CSVProcessor...")
    
    # Utwórz instancję
    processor = CSVProcessor()
    
    # Test 1: Sprawdź dostępne daty dla PODCAST
    print("\n1️⃣ Sprawdzanie dostępnych dat dla kategorii PODCAST...")
    available_dates = processor.get_available_dates("PODCAST")
    print(f"   Dostępne daty: {available_dates}")
    
    if available_dates:
        # Test 2: Pobierz dane dla najnowszej daty
        latest_date = available_dates[0]
        print(f"\n2️⃣ Pobieranie danych dla daty: {latest_date}")
        
        # Konwertuj string na date
        report_date = date.fromisoformat(latest_date)
        
        # Pobierz dane trendów
        trend_data = processor.get_trend_data("PODCAST", report_date)
        
        print(f"   Pobrano {len(trend_data)} rekordów")
        
        if trend_data:
            print(f"   Pierwszy rekord:")
            first_record = trend_data[0]
            for key, value in first_record.items():
                print(f"     {key}: {value}")
        else:
            print("   ❌ Brak danych trendów")
    else:
        print("   ❌ Brak dostępnych dat")
    
    # Test 3: Test funkcji pomocniczej
    print("\n3️⃣ Test funkcji pomocniczej get_trend_data...")
    if available_dates:
        test_date = date.fromisoformat(available_dates[0])
        helper_data = get_trend_data("PODCAST", test_date)
        print(f"   Funkcja pomocnicza zwróciła {len(helper_data)} rekordów")
    
    print("\n✅ Test zakończony!")

if __name__ == "__main__":
    test_csv_processor()
