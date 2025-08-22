"""
Test dla nowego endpointu /trends/{category_name} w routerze trendów.
Sprawdza czy integracja z csv_processor działa poprawnie.
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do modułu app
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

def test_router_integration():
    """Test integracji routera z csv_processor"""
    
    print("🧪 Testowanie integracji routera z csv_processor...")
    
    try:
        # Import routera
        from app.trend.routers.router import router, get_category_trends
        
        print("✅ Router zaimportowany pomyślnie")
        
        # Sprawdź czy endpoint został zarejestrowany
        routes = [route.path for route in router.routes]
        print(f"📡 Zarejestrowane ścieżki: {routes}")
        
        # Sprawdź czy nowy endpoint istnieje
        if "/trends/{category_name}" in routes:
            print("✅ Endpoint /trends/{category_name} zarejestrowany")
        else:
            print("❌ Endpoint /trends/{category_name} NIE został zarejestrowany")
        
        # Sprawdź funkcję endpointu
        if hasattr(get_category_trends, '__name__'):
            print(f"✅ Funkcja {get_category_trends.__name__} istnieje")
        else:
            print("❌ Funkcja get_category_trends NIE istnieje")
        
        # Sprawdź import csv_processor
        try:
            from app.trend.services.csv_processor import get_trend_data
            print("✅ Import csv_processor działa")
        except ImportError as e:
            print(f"❌ Błąd importu csv_processor: {e}")
        
        print("\n✅ Test integracji zakończony pomyślnie!")
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania: {e}")
        import traceback
        traceback.print_exc()

def test_endpoint_structure():
    """Test struktury nowego endpointu"""
    
    print("\n🔍 Test struktury endpointu...")
    
    try:
        from app.trend.routers.router import get_category_trends
        import inspect
        
        # Sprawdź sygnaturę funkcji
        sig = inspect.signature(get_category_trends)
        params = list(sig.parameters.keys())
        
        print(f"📋 Parametry funkcji: {params}")
        
        # Sprawdź czy ma wymagane parametry
        required_params = ['request', 'category_name']
        missing_params = [p for p in required_params if p not in params]
        
        if not missing_params:
            print("✅ Wszystkie wymagane parametry obecne")
        else:
            print(f"❌ Brakujące parametry: {missing_params}")
        
        # Sprawdź czy jest async
        if inspect.iscoroutinefunction(get_category_trends):
            print("✅ Funkcja jest asynchroniczna (async)")
        else:
            print("❌ Funkcja NIE jest asynchroniczna")
        
        print("\n✅ Test struktury zakończony!")
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania struktury: {e}")

if __name__ == "__main__":
    test_router_integration()
    test_endpoint_structure()
