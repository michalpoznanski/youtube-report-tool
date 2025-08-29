"""
Serwis do przetwarzania danych z raportów CSV dla modułu trend.
Zapewnia niezawodne wczytywanie i analizę danych z plików CSV.
"""

try:
    import pandas as pd
    import logging
    from datetime import date, timedelta
    from typing import List, Dict, Any, Optional
    from pathlib import Path
    
    print("✅ Wszystkie importy w csv_processor udane")
except ImportError as e:
    print(f"❌ Błąd importu w csv_processor: {e}")
    import traceback
    traceback.print_exc()
    raise

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Klasa do przetwarzania plików CSV z raportami trendów"""
    
    def __init__(self):
        # Użyj Railway Volume Path zamiast lokalnego katalogu
        from app.config.settings import settings
        self.base_path = settings.reports_path
    
    def get_trend_data(self, category: str, report_date: date) -> List[Dict[str, Any]]:
        """
        Pobiera dane trendów dla danej kategorii i daty.
        
        Args:
            category (str): Nazwa kategorii (np. "PODCAST")
            report_date (date): Data raportu (ignorowana - używa najnowszego dostępnego pliku)
            
        Returns:
            List[Dict[str, Any]]: Lista top 50 wyników z danymi trendów
        """
        try:
            # Znajdź najnowszy dostępny plik CSV dla danej kategorii
            pattern = f"report_{category.upper()}_*.csv"
            csv_files = list(self.base_path.glob(pattern))
            
            if not csv_files:
                print(f"❌ CSV Processor: Nie znaleziono plików CSV dla kategorii {category}")
                logger.warning(f"Nie znaleziono plików CSV dla kategorii {category}")
                return []
            
            # Weź najnowszy plik (sortuj po nazwie)
            latest_file = sorted(csv_files)[-1]
            print(f"🔍 CSV Processor: Używam najnowszego pliku: {latest_file}")
            
            # Wczytaj najnowszy raport
            latest_df = self._load_csv_safely(latest_file)
            if latest_df is None or latest_df.empty:
                print(f"❌ CSV Processor: Nie można wczytać raportu: {latest_file}")
                logger.warning(f"Nie można wczytać raportu: {latest_file}")
                return []
            
            # Znajdź poprzedni plik (dla obliczenia delta)
            if len(csv_files) > 1:
                previous_file = sorted(csv_files)[-2]
                print(f"🔍 CSV Processor: Używam poprzedniego pliku: {previous_file}")
                previous_df = self._load_csv_safely(previous_file)
            else:
                previous_df = None
            
            # Przygotuj dane
            print(f"📊 Przetwarzanie danych: {len(latest_df)} filmów w najnowszym raporcie")
            result_data = self._process_trend_data(latest_df, previous_df)
            
            print(f"✅ CSV Processor: Pomyślnie przetworzono {len(result_data)} rekordów dla kategorii {category}")
            print(f"📈 Statystyki: {len(latest_df)} → {len(result_data)} filmów")
            logger.info(f"Pomyślnie przetworzono {len(result_data)} rekordów dla kategorii {category}")
            return result_data
            
        except Exception as e:
            print(f"❌ CSV Processor: Błąd: {e}")
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
            
            # Sprawdź wymagane kolumny - dostosuj do rzeczywistych plików CSV
            # Obsługuj zarówno stary format (video_id, title, views_today) jak i nowy (Video_ID, Title, View_Count)
            required_columns_old = ['video_id', 'title', 'views_today']
            required_columns_new = ['Video_ID', 'Title', 'View_Count']
            
            # Sprawdź czy mamy stary format
            missing_columns_old = [col for col in required_columns_old if col not in df.columns]
            # Sprawdź czy mamy nowy format
            missing_columns_new = [col for col in required_columns_new if col not in df.columns]
            
            if missing_columns_old and missing_columns_new:
                logger.error(f"Brak wymaganych kolumn w {file_path}. Stary format: {missing_columns_old}, Nowy format: {missing_columns_new}")
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
            
            # Określ format pliku CSV
            is_new_format = 'Video_ID' in today_df.columns and 'Title' in today_df.columns and 'View_Count' in today_df.columns
            is_old_format = 'video_id' in today_df.columns and 'title' in today_df.columns and 'views_today' in today_df.columns
            
            if not (is_new_format or is_old_format):
                logger.error("Nieznany format pliku CSV")
                return []
            
            # Mapuj kolumny na standardowe nazwy
            if is_new_format:
                # Nowy format: Video_ID, Title, View_Count, Duration
                video_id_col = 'Video_ID'
                title_col = 'Title'
                view_count_col = 'View_Count'
                duration_col = 'Duration'
                channel_col = 'Channel_Name'
            else:
                # Stary format: video_id, title, views_today, duration_seconds
                video_id_col = 'video_id'
                title_col = 'title'
                view_count_col = 'views_today'
                duration_col = 'duration_seconds'
                channel_col = 'channel'
            
            # Dodaj kolumnę video_type na podstawie Duration
            def safe_parse_duration(duration_val):
                """Bezpiecznie parsuje Duration i zwraca video_type"""
                try:
                    if pd.isna(duration_val):
                        return "Longform"
                    
                    if is_new_format:
                        # Nowy format: Duration w formacie ISO 8601 (PT1H2M3S)
                        duration_str = str(duration_val)
                        if not duration_str.startswith('PT'):
                            return "Longform"
                        
                        # Parsuj format PT1H2M3S
                        hours = 0
                        minutes = 0
                        seconds = 0
                        
                        # Parsuj godziny (H)
                        if 'H' in duration_str:
                            hours_part = duration_str.split('H')[0]
                            hours = int(hours_part.split('T')[1])
                        
                        # Parsuj minuty (M) - uwaga na kolejność!
                        if 'M' in duration_str:
                            # Znajdź część z minutami (po H, przed S)
                            if 'H' in duration_str:
                                # Format: PT1H2M3S
                                minutes_part = duration_str.split('H')[1].split('M')[0]
                            else:
                                # Format: PT2M3S
                                minutes_part = duration_str.split('M')[0].split('T')[1]
                            minutes = int(minutes_part)
                        
                        # Parsuj sekundy (S)
                        if 'S' in duration_str:
                            # Znajdź część z sekundami (po M lub po T)
                            if 'M' in duration_str:
                                # Format: PT1H2M3S lub PT2M3S
                                seconds_part = duration_str.split('M')[1].split('S')[0]
                            else:
                                # Format: PT3S
                                seconds_part = duration_str.split('T')[1].split('S')[0]
                            seconds = int(seconds_part)
                        
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        # Filmy do 10 minut (600 sekund) to shorts, powyżej to long-form
                        return "Shorts" if total_seconds <= 600 else "Longform"
                    else:
                        # Stary format: duration_seconds jako liczba
                        duration_seconds = int(duration_val)
                        # Filmy do 10 minut (600 sekund) to shorts, powyżej to long-form
                        return "Shorts" if duration_seconds <= 600 else "Longform"
                    
                except (ValueError, TypeError):
                    # W przypadku błędu parsowania, domyślnie Longform
                    return "Longform"
            
            # Debugowanie parsowania Duration
            print(f"🔍 Parsowanie Duration dla {len(result_df)} filmów...")
            
            # Sprawdź problematyczne Duration
            problematic_durations = result_df[result_df[duration_col].isin(['P0D', '', 'nan', 'None'])]
            if not problematic_durations.empty:
                print(f"⚠️ Znaleziono problematyczne Duration:")
                for _, row in problematic_durations.iterrows():
                    print(f"   - {row.get(title_col, '')[:50]}... | Duration: '{row.get(duration_col, '')}' | Views: {row.get(view_count_col, 0)}")
            
            result_df['video_type'] = result_df[duration_col].apply(safe_parse_duration)
            
            # Inicjalizuj kolumnę delta
            result_df['delta'] = 0
            
            # Jeśli mamy wczorajsze dane, oblicz przyrosty
            if yesterday_df is not None and not yesterday_df.empty:
                # Mapuj wczorajsze wyświetlenia po video_id
                yesterday_views = yesterday_df.set_index(video_id_col)[view_count_col].to_dict()
                
                # Oblicz delta
                result_df['delta'] = result_df.apply(
                    lambda row: row[view_count_col] - yesterday_views.get(row[video_id_col], 0), 
                    axis=1
                )
            
            # Dodaj kolumnę thumbnail_url (YouTube thumbnail)
            result_df['thumbnail_url'] = result_df[video_id_col].apply(
                lambda x: f"https://img.youtube.com/vi/{x}/mqdefault.jpg" if pd.notna(x) else ""
            )
            
            # Sortuj malejąco według delta
            result_df = result_df.sort_values('delta', ascending=False)
            
            # Zwróć wszystkie wyniki (nie tylko top 50)
            top_results = result_df
            
            # Konwertuj do listy słowników
            result_list = []
            for _, row in top_results.iterrows():
                # Pomiń zaplanowane transmisje live (0 wyświetleń, niepoprawny Duration)
                views = int(row.get(view_count_col, 0))
                duration = str(row.get(duration_col, ''))
                
                # Filtruj filmy z 0 wyświetleniami lub niepoprawnym Duration
                if views == 0 or duration == 'P0D' or duration == '':
                    print(f"⚠️ Pomijam film: {row.get(title_col, '')[:50]}... (views: {views}, duration: {duration})")
                    continue
                
                result_list.append({
                    'title': str(row.get(title_col, '')),
                    'views': views,
                    'delta': int(row.get('delta', 0)),
                    'video_type': str(row.get('video_type', 'Longform')),
                    'thumbnail_url': str(row.get('thumbnail_url', '')),
                    'video_id': str(row.get(video_id_col, '')),
                    'channel': str(row.get(channel_col, '')),
                    'duration': duration
                })
            
            print(f"✅ Po filtrowaniu: {len(result_list)} filmów (pominięto zaplanowane transmisje live)")
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
