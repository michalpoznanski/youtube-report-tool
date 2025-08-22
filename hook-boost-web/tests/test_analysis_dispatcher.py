"""
Test Analysis Dispatcher - Testy dla modułu CategoryAnalysisDispatcher

Testy sprawdzają:
- Poprawne inicjalizowanie dispatchera dla kategorii PODCAST
- Odrzucanie nieobsługiwanych kategorii
- Integrację z guest_radar.analyzer.GuestRadarAnalyzer
- Obsługę błędów i wyjątków

Autor: Hook Boost Team
Wersja: 1.0.0
Data: 2025-07-29
"""

import unittest
import sys
import os
from pathlib import Path

# Dodaj root projektu do ścieżki Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_dispatcher import CategoryAnalysisDispatcher


class TestCategoryAnalysisDispatcher(unittest.TestCase):
    """
    Testy dla klasy CategoryAnalysisDispatcher
    """
    
    def setUp(self):
        """
        Przygotowanie do testów
        """
        self.test_csv_files = [
            "test_report_2025-07-28.csv",
            "test_report_2025-07-29.csv"
        ]
    
    def test_podcast_category_initialization(self):
        """
        Test inicjalizacji dispatchera dla kategorii PODCAST
        """
        print("\n🧪 Test: Inicjalizacja kategorii PODCAST")
        
        try:
            dispatcher = CategoryAnalysisDispatcher(category="PODCAST")
            
            # Sprawdź czy dispatcher został poprawnie zainicjalizowany
            self.assertEqual(dispatcher.category, "PODCAST")
            self.assertIsNotNone(dispatcher.analyzer)
            
            print("✅ Dispatcher dla kategorii PODCAST zainicjalizowany poprawnie")
            print(f"   Kategoria: {dispatcher.category}")
            print(f"   Analizator: {type(dispatcher.analyzer).__name__}")
            
        except Exception as e:
            self.fail(f"Błąd inicjalizacji dispatchera dla PODCAST: {e}")
    
    def test_podcast_category_analysis(self):
        """
        Test analizy dla kategorii PODCAST
        """
        print("\n🧪 Test: Analiza kategorii PODCAST")
        
        try:
            dispatcher = CategoryAnalysisDispatcher(category="PODCAST")
            
            # Uruchom analizę (pliki nie istnieją, ale powinno działać)
            results = dispatcher.run_analysis(csv_files=self.test_csv_files)
            
            # Sprawdź strukturę wyników
            self.assertIn("category", results)
            self.assertIn("analysis_type", results)
            self.assertIn("analysis_date", results)
            self.assertIn("csv_files_processed", results)
            self.assertIn("total_guests_found", results)
            self.assertIn("analysis_summary", results)
            
            self.assertEqual(results["category"], "PODCAST")
            self.assertEqual(results["analysis_type"], "guest_radar")
            
            print("✅ Analiza kategorii PODCAST zakończona pomyślnie")
            print(f"   Kategoria: {results['category']}")
            print(f"   Typ analizy: {results['analysis_type']}")
            print(f"   Pliki przetworzone: {len(results['csv_files_processed'])}")
            print(f"   Goście znalezieni: {results['total_guests_found']}")
            
        except Exception as e:
            self.fail(f"Błąd analizy dla kategorii PODCAST: {e}")
    
    def test_unsupported_category_rejection(self):
        """
        Test odrzucania nieobsługiwanych kategorii
        """
        print("\n🧪 Test: Odrzucanie nieobsługiwanych kategorii")
        
        unsupported_categories = ["MOTORYZACJA", "POLITYKA", "SHOWBIZ"]
        
        for category in unsupported_categories:
            try:
                dispatcher = CategoryAnalysisDispatcher(category=category)
                self.fail(f"Dispatcher nie powinien zostać zainicjalizowany dla kategorii: {category}")
                
            except NotImplementedError as e:
                print(f"✅ Oczekiwany błąd dla kategorii {category}: {e}")
                self.assertIn("nie jest jeszcze zaimplementowana", str(e))
                
            except Exception as e:
                self.fail(f"Nieoczekiwany błąd dla kategorii {category}: {e}")
    
    def test_invalid_category_rejection(self):
        """
        Test odrzucania nieprawidłowych kategorii
        """
        print("\n🧪 Test: Odrzucanie nieprawidłowych kategorii")
        
        invalid_categories = ["INVALID", "TEST", "RANDOM", ""]
        
        for category in invalid_categories:
            try:
                dispatcher = CategoryAnalysisDispatcher(category=category)
                self.fail(f"Dispatcher nie powinien zostać zainicjalizowany dla nieprawidłowej kategorii: {category}")
                
            except ValueError as e:
                print(f"✅ Oczekiwany błąd dla nieprawidłowej kategorii {category}: {e}")
                self.assertIn("Nieznana kategoria", str(e))
                
            except Exception as e:
                self.fail(f"Nieoczekiwany błąd dla nieprawidłowej kategorii {category}: {e}")
    
    def test_supported_categories_list(self):
        """
        Test listy obsługiwanych kategorii
        """
        print("\n🧪 Test: Lista obsługiwanych kategorii")
        
        try:
            dispatcher = CategoryAnalysisDispatcher(category="PODCAST")
            supported_categories = dispatcher.get_supported_categories()
            
            expected_categories = ["PODCAST", "MOTORYZACJA", "POLITYKA", "SHOWBIZ"]
            
            self.assertEqual(set(supported_categories), set(expected_categories))
            
            print("✅ Lista obsługiwanych kategorii poprawna")
            print(f"   Obsługiwane kategorie: {supported_categories}")
            
        except Exception as e:
            self.fail(f"Błąd pobierania listy kategorii: {e}")
    
    def test_category_status(self):
        """
        Test statusu implementacji kategorii
        """
        print("\n🧪 Test: Status implementacji kategorii")
        
        try:
            dispatcher = CategoryAnalysisDispatcher(category="PODCAST")
            category_status = dispatcher.get_category_status()
            
            expected_status = {
                "PODCAST": "implemented",
                "MOTORYZACJA": "planned",
                "POLITYKA": "planned",
                "SHOWBIZ": "planned"
            }
            
            self.assertEqual(category_status, expected_status)
            
            print("✅ Status implementacji kategorii poprawny")
            print(f"   Status: {category_status}")
            
        except Exception as e:
            self.fail(f"Błąd pobierania statusu kategorii: {e}")
    
    def test_case_insensitive_category(self):
        """
        Test obsługi kategorii niezależnie od wielkości liter
        """
        print("\n🧪 Test: Obsługa kategorii niezależnie od wielkości liter")
        
        try:
            # Test różnych wariantów wielkości liter
            variants = ["podcast", "PODCAST", "Podcast", "PoDcAsT"]
            
            for variant in variants:
                dispatcher = CategoryAnalysisDispatcher(category=variant)
                self.assertEqual(dispatcher.category, "PODCAST")
                self.assertIsNotNone(dispatcher.analyzer)
            
            print("✅ Obsługa kategorii niezależnie od wielkości liter działa poprawnie")
            
        except Exception as e:
            self.fail(f"Błąd obsługi kategorii niezależnie od wielkości liter: {e}")


def run_tests():
    """
    Uruchomienie wszystkich testów
    """
    print("🎯 Test Analysis Dispatcher - Uruchamianie testów")
    print("=" * 60)
    
    # Utwórz test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCategoryAnalysisDispatcher)
    
    # Uruchom testy
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Podsumowanie wyników
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE TESTÓW:")
    print(f"   Testy uruchomione: {result.testsRun}")
    print(f"   Testy zakończone sukcesem: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Testy z błędami: {len(result.errors)}")
    print(f"   Testy z awariami: {len(result.failures)}")
    
    if result.wasSuccessful():
        print("✅ WSZYSTKIE TESTY ZAKOŃCZONE SUKCESEM!")
    else:
        print("❌ NIEKTÓRE TESTY ZAKOŃCZONE BŁĘDEM!")
        
        if result.errors:
            print("\n🔴 BŁĘDY:")
            for test, error in result.errors:
                print(f"   {test}: {error}")
        
        if result.failures:
            print("\n🔴 AWARIE:")
            for test, failure in result.failures:
                print(f"   {test}: {failure}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 