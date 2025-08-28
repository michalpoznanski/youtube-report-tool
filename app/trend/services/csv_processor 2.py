"""
Serwis do przetwarzania danych z raportów CSV dla modułu trend.
Zapewnia niezawodne wczytywanie i analizę danych z plików CSV.
"""

import pandas as pd
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Klasa do przetwarzania plików CSV z raportami trendów"""
    
    def __init__(self):
        # Stała ścieżka do raportów
        self.base_path = Path("/mnt/volume/reports")
    
    def get_trend_data(self, category: str, report_date: date) -> List[Dict[str, Any]]:
        """
        Pobiera dane trendów dla danej kategorii i daty.
        
        Args:
            category (str): Nazwa kategorii (np. "PODCAST")
            report_date (date): Data raportu
            
        Returns:
            List[Dict[str, Any]]: Lista top 50 wyników z danymi trendów
        """
        try:
            # Konstruuj nazwy plików
            today_file = f"report_{category.upper()}_{report_date.strftime('%Y-%m-%d')}.csv"
            yesterday_file = f"report_{category.upper()}_{(report_date - timedelta(days=1)).strftime('%Y-%m-%d')}.csv"
            
            # Ścieżki do plików
            today_path = self.base_path / today_file
            yesterday_path = self.base_path / yesterday_file
            
            logger.info(f"Próba wczytania plików: {today_file}, {yesterday_file}")
            
            # Wczytaj dzisiejszy raport
            today_df = self._load_csv_safely(today_path)
            if today_df is None or today_df.empty:
                logger.warning(f"Nie można wczytać dzisiejszego raportu: {today_file}")
                return []
            
            # Wczytaj wczorajszy raport (opcjonalny)
            yesterday_df = self._load_csv_safely(yesterday_path)
            
            # Przygotuj dane
            result_data = self._process_trend_data(today_df, yesterday_df)
            
            logger.info(f"Pomyślnie przetworzono {len(result_data)} rekordów dla kategorii {category}")
            return result_data
            
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania danych trendów dla {category} {report_date}: {e}")
            return []
    
    def _load_csv_safely(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Bezpiecznie wczytuje plik CSV z obsługą błędów.
        
        Args:
            file_path (Path): Ścieżka do pliku CSV
            
        Returns:
            Optional[pd.DataFrame]: DataFrame z danymi lub None w przypadku błędu
        """
        try:
            if not file_path.exists():
                logger.debug(f"Plik nie istnieje: {file_path}")
                return None
            
            # Wczytaj CSV z obsługą różnych kodowań
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Sprawdź czy DataFrame nie jest pusty
            if df.empty:
                logger.warning(f"Plik CSV jest pusty: {file_path}")
                return None
            
            # Sprawdź wymagane kolumny
            required_columns = ['video_id', 'title', 'views_today', 'duration_seconds']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Brak wymaganych kolumn w {file_path}: {missing_columns}")
                return None
            
            logger.debug(f"Pomyślnie wczytano {len(df)} rekordów z {file_path}")
            return df
            
        except FileNotFoundError:
            logger.debug(f"Plik nie znaleziony: {file_path}")
            return None
        except pd.errors.EmptyDataError:
            logger.warning(f"Plik CSV jest pusty: {file_path}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"Błąd parsowania CSV {file_path}: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Błąd kodowania UTF-8 w {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas wczytywania {file_path}: {e}")
            return None
    
    def _process_trend_data(self, today_df: pd.DataFrame, yesterday_df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Przetwarza dane trendów i oblicza przyrosty.
        
        Args:
            today_df (pd.DataFrame): Dzisiejsze dane
            yesterday_df (Optional[pd.DataFrame]): Wczorajsze dane
            
        Returns:
            List[Dict[str, Any]]: Lista przetworzonych rekordów
        """
        try:
            # Skopiuj dzisiejsze dane
            result_df = today_df.copy()
            
            # Dodaj kolumnę video_type na podstawie duration_seconds
            result_df['video_type'] = result_df['duration_seconds'].apply(
                lambda x: "Shorts" if pd.notna(x) and float(x) <= 600 else "Longform"
            )
            
            # Inicjalizuj kolumnę delta
            result_df['delta'] = 0
            
            # Jeśli mamy wczorajsze dane, oblicz przyrosty
            if yesterday_df is not None and not yesterday_df.empty:
                # Mapuj wczorajsze wyświetlenia po video_id
                yesterday_views = yesterday_df.set_index('video_id')['views_today'].to_dict()
                
                # Oblicz delta
                result_df['delta'] = result_df.apply(
                    lambda row: row['views_today'] - yesterday_views.get(row['video_id'], 0), 
                    axis=1
                )
            
            # Dodaj kolumnę thumbnail_url (YouTube thumbnail)
            result_df['thumbnail_url'] = result_df['video_id'].apply(
                lambda x: f"https://img.youtube.com/vi/{x}/mqdefault.jpg" if pd.notna(x) else ""
            )
            
            # Sortuj malejąco według delta
            result_df = result_df.sort_values('delta', ascending=False)
            
            # Wybierz top 50 wyników
            top_results = result_df.head(50)
            
            # Konwertuj do listy słowników
            result_list = []
            for _, row in top_results.iterrows():
                result_list.append({
                    'title': str(row.get('title', '')),
                    'views': int(row.get('views_today', 0)),
                    'delta': int(row.get('delta', 0)),
                    'video_type': str(row.get('video_type', 'Longform')),
                    'thumbnail_url': str(row.get('thumbnail_url', '')),
                    'video_id': str(row.get('video_id', '')),
                    'channel': str(row.get('channel', '')),
                    'duration_seconds': int(row.get('duration_seconds', 0)) if pd.notna(row.get('duration_seconds')) else 0
                })
            
            return result_list
            
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania danych trendów: {e}")
            return []
    
    def get_available_dates(self, category: str) -> List[str]:
        """
        Zwraca listę dostępnych dat dla danej kategorii.
        
        Args:
            category (str): Nazwa kategorii
            
        Returns:
            List[str]: Lista dat w formacie YYYY-MM-DD
        """
        try:
            if not self.base_path.exists():
                logger.warning(f"Katalog raportów nie istnieje: {self.base_path}")
                return []
            
            # Wzorzec pliku
            pattern = f"report_{category.upper()}_*.csv"
            
            # Znajdź pliki
            csv_files = list(self.base_path.glob(pattern))
            
            # Wyciągnij daty z nazw plików
            dates = []
            for file_path in csv_files:
                try:
                    # Format: report_PODCAST_2025-08-13.csv
                    filename = file_path.stem  # bez rozszerzenia
                    date_part = filename.split('_')[-1]
                    
                    # Sprawdź czy to poprawna data
                    date.fromisoformat(date_part)
                    dates.append(date_part)
                except (ValueError, IndexError):
                    continue
            
            # Sortuj daty malejąco (najnowsze pierwsze)
            dates.sort(reverse=True)
            
            logger.info(f"Znaleziono {len(dates)} dostępnych dat dla kategorii {category}")
            return dates
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania dostępnych dat dla {category}: {e}")
            return []


# Funkcja pomocnicza dla łatwiejszego dostępu
def get_trend_data(category: str, report_date: date) -> List[Dict[str, Any]]:
    """
    Funkcja pomocnicza do pobierania danych trendów.
    
    Args:
        category (str): Nazwa kategorii
        report_date (date): Data raportu
        
    Returns:
        List[Dict[str, Any]]: Lista danych trendów
    """
    processor = CSVProcessor()
    return processor.get_trend_data(category, report_date)
