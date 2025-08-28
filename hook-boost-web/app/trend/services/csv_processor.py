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
        # Użyj tej samej ścieżki co API routes
        self.base_path = Path("/mnt/volume/reports")
    
    def get_trend_data(self, category: str, report_date: date) -> List[Dict[str, Any]]:
        """
        Pobiera dane trendów dla danej kategorii i daty.
        Używa tej samej logiki co API routes.
        """
        try:
            print(f"🚀 CSV Processor: Start dla kategorii {category}, data {report_date}")
            
            # Użyj tej samej logiki co API routes
            import os
            reports_dir = "/mnt/volume/reports"
            
            if not os.path.exists(reports_dir):
                print(f"❌ CSV Processor: Katalog {reports_dir} nie istnieje!")
                return []
            
            # Znajdź pliki CSV dla kategorii
            csv_files = []
            for file in os.listdir(reports_dir):
                if file.startswith(f"report_{category.upper()}_") and file.endswith('.csv'):
                    csv_files.append(file)
            
            print(f"📁 CSV Processor: Znalezione pliki: {csv_files}")
            
            if not csv_files:
                print(f"❌ CSV Processor: Brak plików CSV dla kategorii {category}")
                return []
            
            # Użyj najnowszego pliku
            latest_file = sorted(csv_files)[-1]  # Ostatni alfabetycznie = najnowszy
            file_path = os.path.join(reports_dir, latest_file)
            
            print(f"📁 CSV Processor: Używam pliku: {latest_file}")
            
            # Wczytaj CSV używając pandas
            import pandas as pd
            df = pd.read_csv(file_path)
            
            print(f"✅ CSV Processor: Wczytano {len(df)} wierszy z {latest_file}")
            
            # Konwertuj do listy słowników
            result_list = []
            for _, row in df.iterrows():
                result_list.append({
                    'title': str(row.get('Title', '')),
                    'views': int(row.get('View_Count', 0)),
                    'delta': 0,  # Na razie bez delta
                    'video_type': str(row.get('video_type', 'Longform')),
                    'thumbnail_url': f"https://img.youtube.com/vi/{row.get('Video_ID', '')}/mqdefault.jpg",
                    'video_id': str(row.get('Video_ID', '')),
                    'channel': str(row.get('Channel_Name', '')),
                    'duration': str(row.get('Duration', '')),
                    'description': str(row.get('Description', '')),
                    'tags': str(row.get('Tags', '')),
                    'like_count': int(row.get('Like_Count', 0)),
                    'topic_categories': str(row.get('Topic_Categories', '')),
                    'channel_id': str(row.get('Channel_ID', '')),
                    'date_published': str(row.get('Date_of_Publishing', '')),
                    'hour_published': str(row.get('Hour_GMT2', ''))
                })
            
            print(f"✅ CSV Processor: Zwracam {len(result_list)} wideo")
            return result_list
            
        except Exception as e:
            print(f"❌ CSV Processor: Błąd: {e}")
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
            print(f"🔍 CSV Processor: Próba wczytania pliku: {file_path}")
            print(f"🔍 CSV Processor: Plik istnieje: {file_path.exists()}")
            
            if not file_path.exists():
                print(f"❌ CSV Processor: Plik nie istnieje: {file_path}")
                logger.debug(f"Plik nie istnieje: {file_path}")
                return None
            
            # Sprawdź rozmiar pliku
            file_size = file_path.stat().st_size
            print(f"🔍 CSV Processor: Rozmiar pliku: {file_size} bajtów")
            
            if file_size == 0:
                print(f"❌ CSV Processor: Plik jest pusty: {file_path}")
                logger.warning(f"Plik CSV jest pusty: {file_path}")
                return None
            
            # Wczytaj CSV z obsługą różnych kodowań
            print(f"🔍 CSV Processor: Wczytuję CSV...")
            df = pd.read_csv(file_path, encoding='utf-8')
            print(f"✅ CSV Processor: Pomyślnie wczytano CSV: {len(df)} wierszy, {len(df.columns)} kolumn")
            
            # Sprawdź czy DataFrame nie jest pusty
            if df.empty:
                print(f"❌ CSV Processor: DataFrame jest pusty: {file_path}")
                logger.warning(f"Plik CSV jest pusty: {file_path}")
                return None
            
            # Sprawdź pierwsze kilka wierszy
            print(f"🔍 CSV Processor: Pierwsze 3 wiersze:")
            print(df.head(3))
            
            return df
            
        except Exception as e:
            print(f"❌ CSV Processor: Błąd podczas wczytywania {file_path}: {e}")
            logger.error(f"Błąd podczas wczytywania CSV {file_path}: {e}")
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
            
            # Dodaj kolumnę video_type na podstawie Duration
            result_df['video_type'] = result_df['Duration'].apply(
                lambda x: "Shorts" if pd.notna(x) and str(x).startswith('PT') and 'S' in str(x) and int(str(x).split('S')[0].split('T')[-1]) <= 180 else "Longform"
            )
            
            # Inicjalizuj kolumnę delta
            result_df['delta'] = 0
            
            # Jeśli mamy wczorajsze dane, oblicz przyrosty
            if yesterday_df is not None and not yesterday_df.empty:
                # Mapuj wczorajsze wyświetlenia po video_id
                yesterday_views = yesterday_df.set_index('Video_ID')['View_Count'].to_dict()
                
                # Oblicz delta
                result_df['delta'] = result_df.apply(
                    lambda row: row['View_Count'] - yesterday_views.get(row['Video_ID'], 0), 
                    axis=1
                )
            
            # Dodaj kolumnę thumbnail_url (YouTube thumbnail)
            result_df['thumbnail_url'] = result_df['Video_ID'].apply(
                lambda x: f"https://img.youtube.com/vi/{x}/mqdefault.jpg" if pd.notna(x) else ""
            )
            
            # Sortuj malejąco według delta
            result_df = result_df.sort_values('delta', ascending=False)
            
            # Zwróć wszystkie wyniki (nie tylko top 50)
            top_results = result_df
            
            # Konwertuj do listy słowników
            result_list = []
            for _, row in top_results.iterrows():
                result_list.append({
                    'title': str(row.get('Title', '')),
                    'views': int(row.get('View_Count', 0)),
                    'delta': int(row.get('delta', 0)),
                    'video_type': str(row.get('video_type', 'Longform')),
                    'thumbnail_url': str(row.get('thumbnail_url', '')),
                    'video_id': str(row.get('Video_ID', '')),
                    'channel': str(row.get('Channel_Name', '')),
                    'duration': str(row.get('Duration', '')),
                    'description': str(row.get('Description', '')),
                    'tags': str(row.get('Tags', '')),
                    'like_count': int(row.get('Like_Count', 0)),
                    'topic_categories': str(row.get('Topic_Categories', '')),
                    'channel_id': str(row.get('Channel_ID', '')),
                    'date_published': str(row.get('Date_of_Publishing', '')),
                    'hour_published': str(row.get('Hour_GMT2', ''))
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
