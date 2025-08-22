"""
Przykład integracji CSVProcessor z istniejącym routerem trend.
Pokazuje jak zastąpić obecną logikę ładowania CSV.
"""

from datetime import date
from typing import List, Dict, Any

# Import nowego serwisu
from .csv_processor import get_trend_data, CSVProcessor

def example_router_integration():
    """
    Przykład jak zintegrować CSVProcessor z routerem trend.
    """
    
    print("🔗 Przykład integracji CSVProcessor z routerem...")
    
    # Przykład 1: Zastąpienie funkcji load_latest w routerze
    print("\n1️⃣ Zastąpienie load_latest w routerze:")
    
    # Stara logika (obecna w app/trend/core/loader.py):
    # df, report_date = load_latest(category)
    
    # Nowa logika z CSVProcessor:
    category = "PODCAST"
    report_date = date.today()
    
    try:
        trend_data = get_trend_data(category, report_date)
        
        if trend_data:
            print(f"   ✅ Pobrano {len(trend_data)} rekordów trendów")
            print(f"   📊 Pierwszy rekord:")
            first_record = trend_data[0]
            for key, value in first_record.items():
                print(f"      {key}: {value}")
        else:
            print(f"   ⚠️ Brak danych trendów dla {category}")
            
    except Exception as e:
        print(f"   ❌ Błąd: {e}")
    
    # Przykład 2: Użycie w endpoincie API
    print("\n2️⃣ Użycie w endpoincie API:")
    
    def api_endpoint_example(category: str, report_date: date) -> Dict[str, Any]:
        """
        Przykład endpointu API używającego CSVProcessor
        """
        try:
            # Pobierz dane trendów
            trend_data = get_trend_data(category, report_date)
            
            # Przygotuj odpowiedź
            response = {
                "success": True,
                "category": category,
                "report_date": report_date.isoformat(),
                "total_records": len(trend_data),
                "data": trend_data
            }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "report_date": report_date.isoformat()
            }
    
    # Test endpointu
    response = api_endpoint_example("PODCAST", date.today())
    print(f"   📡 Odpowiedź API: {response['success']}")
    print(f"   📊 Liczba rekordów: {response['total_records']}")
    
    # Przykład 3: Użycie w szablonie Jinja2
    print("\n3️⃣ Użycie w szablonie Jinja2:")
    
    def template_context_example(category: str, report_date: date) -> Dict[str, Any]:
        """
        Przykład kontekstu dla szablonu Jinja2
        """
        trend_data = get_trend_data(category, report_date)
        
        # Podziel dane na kategorie
        shorts = [item for item in trend_data if item['video_type'] == 'Shorts']
        longform = [item for item in trend_data if item['video_type'] == 'Longform']
        
        # Oblicz statystyki
        total_views = sum(item['views'] for item in trend_data)
        total_delta = sum(item['delta'] for item in trend_data)
        
        return {
            "category": category,
            "report_date": report_date.isoformat(),
            "trend_data": trend_data,
            "shorts": shorts,
            "longform": longform,
            "stats": {
                "total_records": len(trend_data),
                "total_views": total_views,
                "total_delta": total_delta,
                "shorts_count": len(shorts),
                "longform_count": len(longform)
            }
        }
    
    # Test kontekstu szablonu
    context = template_context_example("PODCAST", date.today())
    print(f"   🎨 Kontekst szablonu:")
    print(f"      Kategoria: {context['category']}")
    print(f"      Data: {context['report_date']}")
    print(f"      Shorts: {context['stats']['shorts_count']}")
    print(f"      Longform: {context['stats']['longform_count']}")
    
    print("\n✅ Przykład integracji zakończony!")

def example_error_handling():
    """
    Przykład obsługi błędów w CSVProcessor
    """
    
    print("\n🛡️ Przykład obsługi błędów:")
    
    processor = CSVProcessor()
    
    # Test z nieistniejącą kategorią
    print("\n1️⃣ Test z nieistniejącą kategorią:")
    non_existent_data = processor.get_trend_data("NON_EXISTENT", date.today())
    print(f"   Wynik: {len(non_existent_data)} rekordów (oczekiwane: 0)")
    
    # Test z nieistniejącą datą
    print("\n2️⃣ Test z nieistniejącą datą:")
    future_date = date(2030, 1, 1)
    future_data = processor.get_trend_data("PODCAST", future_date)
    print(f"   Wynik: {len(future_data)} rekordów (oczekiwane: 0)")
    
    # Test dostępnych dat
    print("\n3️⃣ Test dostępnych dat:")
    available_dates = processor.get_available_dates("PODCAST")
    print(f"   Dostępne daty: {available_dates}")
    
    print("\n✅ Przykład obsługi błędów zakończony!")

if __name__ == "__main__":
    example_router_integration()
    example_error_handling()
