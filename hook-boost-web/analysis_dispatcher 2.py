"""
Analysis Dispatcher - Centralny moduł do obsługi analiz per kategoria

Ten moduł służy jako dispatcher (rozdzielacz) dla różnych typów analiz
w zależności od kategorii treści. Każda kategoria może mieć własny
specjalizowany moduł analizy.

Obsługiwane kategorie:
- PODCAST -> guest_radar.analyzer.GuestRadarAnalyzer (analiza gości)
- MOTORYZACJA -> auto_radar (planowany)
- POLITYKA -> politics_radar (planowany)
- SHOWBIZ -> showbiz_radar (planowany)

Autor: Hook Boost Team
Wersja: 1.0.0
Data: 2025-07-29
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CategoryAnalysisDispatcher:
    """
    Dispatcher do obsługi analiz per kategoria treści
    """
    
    def __init__(self, category: str):
        """
        Inicjalizacja dispatchera dla określonej kategorii
        
        Args:
            category: Kategoria treści do analizy (np. "PODCAST", "MOTORYZACJA")
        """
        self.category = category.upper()
        self.analyzer = None
        self._initialize_analyzer()
        logger.info(f"CategoryAnalysisDispatcher zainicjalizowany dla kategorii: {self.category}")
    
    def _initialize_analyzer(self):
        """
        Inicjalizuje odpowiedni analizator dla kategorii
        """
        try:
            if self.category == "PODCAST":
                # Import i inicjalizacja Guest Radar Analyzer
                from guest_radar.analyzer import GuestRadarAnalyzer
                self.analyzer = GuestRadarAnalyzer()
                logger.info("✅ Załadowano GuestRadarAnalyzer dla kategorii PODCAST")
                
            elif self.category == "MOTORYZACJA":
                # TODO: implement AUTO_RADAR for MOTORYZACJA
                # from auto_radar.analyzer import AutoRadarAnalyzer
                # self.analyzer = AutoRadarAnalyzer()
                raise NotImplementedError(
                    f"Analiza dla kategorii '{self.category}' nie jest jeszcze zaimplementowana. "
                    "Planowany moduł: AUTO_RADAR"
                )
                
            elif self.category == "POLITYKA":
                # TODO: implement POLITICS_RADAR for POLITYKA
                # from politics_radar.analyzer import PoliticsRadarAnalyzer
                # self.analyzer = PoliticsRadarAnalyzer()
                raise NotImplementedError(
                    f"Analiza dla kategorii '{self.category}' nie jest jeszcze zaimplementowana. "
                    "Planowany moduł: POLITICS_RADAR"
                )
                
            elif self.category == "SHOWBIZ":
                # TODO: implement SHOWBIZ_RADAR for SHOWBIZ
                # from showbiz_radar.analyzer import ShowbizRadarAnalyzer
                # self.analyzer = ShowbizRadarAnalyzer()
                raise NotImplementedError(
                    f"Analiza dla kategorii '{self.category}' nie jest jeszcze zaimplementowana. "
                    "Planowany moduł: SHOWBIZ_RADAR"
                )
                
            else:
                raise ValueError(
                    f"Nieznana kategoria: '{self.category}'. "
                    f"Obsługiwane kategorie: PODCAST, MOTORYZACJA, POLITYKA, SHOWBIZ"
                )
                
        except ImportError as e:
            logger.error(f"Błąd importu modułu dla kategorii {self.category}: {e}")
            raise
        except Exception as e:
            logger.error(f"Błąd inicjalizacji analizatora dla kategorii {self.category}: {e}")
            raise
    
    def run_analysis(self, csv_files: List[str], output_directory: Optional[str] = None) -> Dict:
        """
        Uruchamia analizę dla określonej kategorii
        
        Args:
            csv_files: Lista ścieżek do plików CSV do analizy
            output_directory: Katalog wyjściowy dla raportów (opcjonalny)
            
        Returns:
            Słownik z wynikami analizy
        """
        if not self.analyzer:
            raise RuntimeError(f"Analizator dla kategorii '{self.category}' nie został zainicjalizowany")
        
        logger.info(f"Rozpoczęcie analizy dla kategorii '{self.category}'")
        logger.info(f"Pliki do analizy: {csv_files}")
        
        try:
            if self.category == "PODCAST":
                return self._run_podcast_analysis(csv_files, output_directory)
            else:
                # Dla innych kategorii (gdy zostaną zaimplementowane)
                return self.analyzer.analyze_multiple_reports(csv_files)
                
        except Exception as e:
            logger.error(f"Błąd podczas analizy dla kategorii '{self.category}': {e}")
            raise
    
    def _run_podcast_analysis(self, csv_files: List[str], output_directory: Optional[str] = None) -> Dict:
        """
        Specjalizowana analiza dla kategorii PODCAST
        
        Args:
            csv_files: Lista ścieżek do plików CSV
            output_directory: Katalog wyjściowy
            
        Returns:
            Słownik z wynikami analizy gości podcastów
        """
        logger.info("🎯 Uruchamianie analizy gości podcastów (Guest Radar)")
        
        results = {
            "category": self.category,
            "analysis_type": "guest_radar",
            "analysis_date": datetime.now().isoformat(),
            "csv_files_processed": [],
            "total_guests_found": 0,
            "popularity_scores": {},
            "analysis_summary": {}
        }
        
        # Analiza każdego pliku CSV
        for csv_file in csv_files:
            try:
                logger.info(f"Analizuję plik: {csv_file}")
                
                # Sprawdź czy plik istnieje
                if not Path(csv_file).exists():
                    logger.warning(f"Plik nie istnieje: {csv_file}")
                    continue
                
                # Uruchom analizę pojedynczego pliku
                file_result = self.analyzer.analyze_csv_report(csv_file)
                
                # Dodaj wyniki do ogólnych rezultatów
                results["csv_files_processed"].append({
                    "file": csv_file,
                    "guests_found": file_result.get("guests_found", 0),
                    "total_videos": file_result.get("total_videos", 0),
                    "popularity_score": file_result.get("popularity_score", 0.0)
                })
                
                results["total_guests_found"] += file_result.get("guests_found", 0)
                
                logger.info(f"✅ Analiza pliku {csv_file} zakończona")
                
            except Exception as e:
                logger.error(f"Błąd podczas analizy pliku {csv_file}: {e}")
                results["csv_files_processed"].append({
                    "file": csv_file,
                    "error": str(e)
                })
        
        # Podsumowanie analizy
        results["analysis_summary"] = {
            "files_analyzed": len([f for f in results["csv_files_processed"] if "error" not in f]),
            "files_with_errors": len([f for f in results["csv_files_processed"] if "error" in f]),
            "total_guests": results["total_guests_found"],
            "average_popularity_score": sum([
                f.get("popularity_score", 0.0) for f in results["csv_files_processed"] 
                if "error" not in f
            ]) / max(1, len([f for f in results["csv_files_processed"] if "error" not in f]))
        }
        
        logger.info(f"✅ Analiza kategorii '{self.category}' zakończona")
        logger.info(f"📊 Podsumowanie: {results['analysis_summary']}")
        
        return results
    
    def get_supported_categories(self) -> List[str]:
        """
        Zwraca listę obsługiwanych kategorii
        
        Returns:
            Lista obsługiwanych kategorii
        """
        return ["PODCAST", "MOTORYZACJA", "POLITYKA", "SHOWBIZ"]
    
    def get_category_status(self) -> Dict[str, str]:
        """
        Zwraca status implementacji dla każdej kategorii
        
        Returns:
            Słownik z statusem implementacji kategorii
        """
        return {
            "PODCAST": "implemented",
            "MOTORYZACJA": "planned",
            "POLITYKA": "planned", 
            "SHOWBIZ": "planned"
        }


# Funkcja główna do testowania
def main():
    """
    Funkcja główna do testowania dispatchera
    """
    print("🎯 Category Analysis Dispatcher - Test modułu")
    print("=" * 50)
    
    # Test dla kategorii PODCAST
    try:
        dispatcher = CategoryAnalysisDispatcher(category="PODCAST")
        print(f"✅ Dispatcher zainicjalizowany dla kategorii: {dispatcher.category}")
        
        # Test analizy (bez rzeczywistych plików)
        test_files = ["test_report_1.csv", "test_report_2.csv"]
        results = dispatcher.run_analysis(csv_files=test_files)
        print(f"📊 Wyniki testu: {results}")
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
    
    # Test dla nieobsługiwanej kategorii
    try:
        dispatcher = CategoryAnalysisDispatcher(category="MOTORYZACJA")
    except NotImplementedError as e:
        print(f"✅ Oczekiwany błąd dla nieobsługiwanej kategorii: {e}")
    
    print("\n🔧 Dispatcher gotowy do użycia")


if __name__ == "__main__":
    main() 