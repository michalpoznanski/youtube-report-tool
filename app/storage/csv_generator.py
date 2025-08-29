try:
    import pandas as pd
    from typing import List, Dict, Any
    from datetime import datetime
    import pytz
    import logging
    from pathlib import Path
    from ..config import settings
    import re
    
    print("✅ Wszystkie importy w CSVGenerator udane")
except ImportError as e:
    print(f"❌ Błąd importu w CSVGenerator: {e}")
    import traceback
    traceback.print_exc()
    raise

logger = logging.getLogger(__name__)


class CSVGenerator:
    """Generator raportów CSV z danych YouTube"""
    
    def __init__(self):
        self.columns = [
            'Channel_Name',
            'Channel_ID', 
            'Date_of_Publishing',
            'Hour_GMT2',
            'Title',
            'Description',
            'Tags',
            'video_type',
            'View_Count',
            'Like_Count',
            'Comment_Count',
            'Favorite_Count',
            'Definition',
            'Has_Captions',
            'Licensed_Content',
            'Topic_Categories',
            # 'Names_Extracted',  # Usunięte - niepotrzebne
            'Video_ID',
            'Duration',
            'Thumbnail_URL'
        ]
    
    def generate_csv(self, videos_data: List[Dict], category: str = "general") -> str:
        """Generuje plik CSV z danymi filmów"""
        try:
            # Przygotuj dane
            rows = []
            for video in videos_data:
                # Wyciągnij nazwiska - WYŁĄCZONE
                # from ..analysis import NameExtractor
                # extractor = NameExtractor()
                # names = extractor.extract_from_video_data(video)
                
                # Określ typ filmu (shorts vs long)
                video_type = self._determine_video_type(video.get('duration', ''), video.get('id', ''), video.get('url', ''))
                
                # Przygotuj datę (offset-aware)
                published_at = datetime.fromisoformat(
                    video['published_at'].replace('Z', '+00:00')
                )
                # Upewnij się, że ma strefę czasową UTC
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=pytz.utc)
                date_str = published_at.strftime('%Y-%m-%d')
                hour_str = published_at.strftime('%H:%M')
                
                row = {
                    'Channel_Name': video.get('channel_title', ''),
                    'Channel_ID': video.get('channel_id', ''),
                    'Date_of_Publishing': date_str,
                    'Hour_GMT2': hour_str,
                    'Title': video.get('title', ''),
                    'Description': video.get('description', ''),
                    'Tags': ', '.join(video.get('tags', [])),
                    'video_type': video_type,
                    'View_Count': video.get('view_count', 0),
                    'Like_Count': video.get('like_count', 0),
                    'Comment_Count': video.get('comment_count', 0),
                    'Favorite_Count': video.get('favorite_count', 0),
                    'Definition': video.get('definition', ''),
                    'Has_Captions': video.get('caption', ''),
                    'Licensed_Content': video.get('licensed_content', False),
                    'Topic_Categories': video.get('category_id', ''),
                    # 'Names_Extracted': ', '.join(names),  # Usunięte
                    'Video_ID': video.get('id', ''),
                    'Duration': video.get('duration', ''),
                    'Thumbnail_URL': video.get('thumbnail', '')
                }
                rows.append(row)
            
            # Utwórz DataFrame
            df = pd.DataFrame(rows, columns=self.columns)
            
            # Generuj nazwę pliku w nowym formacie: report_{KATEGORIA}_{DATA_DANYCH}.csv
            # Użyj daty z danych (ostatni film) zamiast daty generowania
            if rows:
                # Znajdź najnowszą datę w danych
                latest_date = max(row['Date_of_Publishing'] for row in rows if row['Date_of_Publishing'])
                filename = f"report_{category.upper()}_{latest_date}.csv"
            else:
                # Fallback - użyj dzisiejszej daty
                timestamp = datetime.now().strftime('%Y-%m-%d')
                filename = f"report_{category.upper()}_{timestamp}.csv"
            
            filepath = settings.reports_path / filename
            
            # Upewnij się, że katalog raportów istnieje
            settings.reports_path.mkdir(parents=True, exist_ok=True)
            
            # Zapisz CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            print(f"📊 Wygenerowano raport CSV: {filepath.absolute()}")
            print(f"   📄 Nazwa pliku: {filename}")
            print(f"   📁 Katalog: {settings.reports_path.absolute()}")
            print(f"   📈 Liczba wierszy: {len(df)}")
            print(f"   💾 Rozmiar pliku: {filepath.stat().st_size} bytes")
            
            logger.info(f"Wygenerowano CSV: {filepath}")
            logger.info(f"Raport CSV: {filename}, {len(df)} wierszy, {filepath.stat().st_size} bytes")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania CSV: {e}")
            raise
    
    def _determine_video_type(self, duration: str, video_id: str = None, video_url: str = None) -> str:
        """Określa typ filmu na podstawie długości i URL"""
        if not duration:
            return "unknown"
        
        # Konwertuj ISO 8601 duration na sekundy
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Sprawdź czy URL zawiera "/shorts/"
            is_shorts_url = False
            if video_url and "/shorts/" in video_url:
                is_shorts_url = True
            elif video_id:
                # Sprawdź czy film może być dostępny jako shorts
                # YouTube Shorts URL format: https://www.youtube.com/shorts/VIDEO_ID
                shorts_url = f"https://www.youtube.com/shorts/{video_id}"
                # Dla uproszczenia, jeśli duration <= 10 min (600s), uznajemy za potencjalny shorts
                if total_seconds <= 600:
                    is_shorts_url = True
            
            # Logika: Jeśli duration <= 10 min (600s) to SHORTS, inaczej LONG
            if total_seconds <= 600:
                return "shorts"
            else:
                return "long"
        
        return "unknown"
    
    def generate_summary_csv(self, all_data: Dict[str, List[Dict]]) -> str:
        """Generuje podsumowanie CSV ze wszystkich kategorii"""
        try:
            all_rows = []
            
            for category, videos in all_data.items():
                for video in videos:
                    # Wyciągnij nazwiska
                    from ..analysis import NameExtractor
                    extractor = NameExtractor()
                    names = extractor.extract_from_video_data(video)
                    
                    # Określ typ filmu (shorts vs long)
                    video_type = self._determine_video_type(video.get('duration', ''), video.get('id', ''), video.get('url', ''))
                    
                    # Przygotuj datę (offset-aware)
                    published_at = datetime.fromisoformat(
                        video['published_at'].replace('Z', '+00:00')
                    )
                    # Upewnij się, że ma strefę czasową UTC
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=pytz.utc)
                    date_str = published_at.strftime('%Y-%m-%d')
                    hour_str = published_at.strftime('%H:%M')
                    
                    row = {
                        'Channel_Name': video.get('channel_title', ''),
                        'Channel_ID': video.get('channel_id', ''),
                        'Date_of_Publishing': date_str,
                        'Hour_GMT2': hour_str,
                        'Title': video.get('title', ''),
                        'Description': video.get('description', ''),
                        'Tags': ', '.join(video.get('tags', [])),
                        'video_type': video_type,
                        'View_Count': video.get('view_count', 0),
                        'Like_Count': video.get('like_count', 0),
                        'Comment_Count': video.get('comment_count', 0),
                        'Favorite_Count': video.get('favorite_count', 0),
                        'Definition': video.get('definition', ''),
                        'Has_Captions': video.get('caption', ''),
                        'Licensed_Content': video.get('licensed_content', False),
                        'Topic_Categories': video.get('category_id', ''),
                        'Names_Extracted': ', '.join(names),
                        'Video_ID': video.get('id', ''),
                        'Duration': video.get('duration', ''),
                        'Thumbnail_URL': video.get('thumbnail', ''),
                        'Category': category
                    }
                    all_rows.append(row)
            
            # Generuj nazwę pliku w nowym formacie: report_SUMMARY_{YYYY-MM-DD}.csv
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f"report_SUMMARY_{timestamp}.csv"
            filepath = settings.reports_path / filename
            
            # Upewnij się, że katalog raportów istnieje
            settings.reports_path.mkdir(parents=True, exist_ok=True)
            
            # Utwórz DataFrame z odpowiednimi kolumnami
            df = pd.DataFrame(all_rows, columns=self.columns + ['Category'])
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            print(f"📊 Wygenerowano raport podsumowujący CSV: {filepath.absolute()}")
            print(f"   📄 Nazwa pliku: {filename}")
            print(f"   📁 Katalog: {settings.reports_path.absolute()}")
            print(f"   📈 Liczba wierszy: {len(df)}")
            print(f"   💾 Rozmiar pliku: {filepath.stat().st_size} bytes")
            
            logger.info(f"Wygenerowano podsumowanie CSV: {filepath}")
            logger.info(f"Raport podsumowujący CSV: {filename}, {len(df)} wierszy, {filepath.stat().st_size} bytes")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania podsumowania CSV: {e}")
            raise

    def rename_old_reports(self) -> Dict[str, Any]:
        """Przemianowuje stare raporty na nowy format nazewnictwa"""
        renamed_count = 0
        errors = []
        renamed_files = []
        
        try:
            print(f"🔄 Rozpoczynam przemianowanie starych raportów...")
            print(f"📁 Katalog raportów: {settings.reports_path.absolute()}")
            
            # Upewnij się, że katalog istnieje
            settings.reports_path.mkdir(parents=True, exist_ok=True)
            
            for file_path in settings.reports_path.glob("*.csv"):
                old_name = file_path.name
                
                # Sprawdź czy to stary format: {category}_{YYYYMMDD_HHMMSS}.csv
                # lub summary_{YYYYMMDD_HHMMSS}.csv
                if re.match(r'^[A-Z_]+_\d{8}_\d{6}\.csv$', old_name):
                    # Wyciągnij kategorię i datę
                    parts = old_name.replace('.csv', '').split('_')
                    if len(parts) >= 3:
                        category = parts[0]
                        date_part = parts[1]  # YYYYMMDD
                        
                        # Konwertuj YYYYMMDD na YYYY-MM-DD
                        try:
                            date_obj = datetime.strptime(date_part, '%Y%m%d')
                            new_date = date_obj.strftime('%Y-%m-%d')
                            
                            # Określ nową nazwę
                            if category.lower() == 'summary':
                                new_name = f"report_SUMMARY_{new_date}.csv"
                            else:
                                new_name = f"report_{category.upper()}_{new_date}.csv"
                            
                            # Sprawdź czy plik o nowej nazwie już istnieje
                            new_path = file_path.parent / new_name
                            if new_path.exists():
                                # Dodaj timestamp do nazwy aby uniknąć konfliktu
                                timestamp = datetime.now().strftime('%H%M%S')
                                new_name = f"report_{category.upper()}_{new_date}_{timestamp}.csv"
                                new_path = file_path.parent / new_name
                            
                            # Przemianuj plik
                            file_path.rename(new_path)
                            renamed_count += 1
                            renamed_files.append({
                                'old_name': old_name,
                                'new_name': new_name
                            })
                            print(f"✅ Przemianowano: {old_name} → {new_name}")
                            
                        except ValueError as e:
                            error_msg = f"Nieprawidłowa data w {old_name}: {e}"
                            errors.append(error_msg)
                            print(f"❌ {error_msg}")
                
                elif re.match(r'^summary_\d{8}_\d{6}\.csv$', old_name):
                    # Specjalny przypadek dla summary
                    parts = old_name.replace('.csv', '').split('_')
                    if len(parts) >= 3:
                        date_part = parts[1]  # YYYYMMDD
                        
                        try:
                            date_obj = datetime.strptime(date_part, '%Y%m%d')
                            new_date = date_obj.strftime('%Y-%m-%d')
                            new_name = f"report_SUMMARY_{new_date}.csv"
                            
                            # Sprawdź czy plik o nowej nazwie już istnieje
                            new_path = file_path.parent / new_name
                            if new_path.exists():
                                # Dodaj timestamp do nazwy aby uniknąć konfliktu
                                timestamp = datetime.now().strftime('%H%M%S')
                                new_name = f"report_SUMMARY_{new_date}_{timestamp}.csv"
                                new_path = file_path.parent / new_name
                            
                            # Przemianuj plik
                            file_path.rename(new_path)
                            renamed_count += 1
                            renamed_files.append({
                                'old_name': old_name,
                                'new_name': new_name
                            })
                            print(f"✅ Przemianowano: {old_name} → {new_name}")
                            
                        except ValueError as e:
                            error_msg = f"Nieprawidłowa data w {old_name}: {e}"
                            errors.append(error_msg)
                            print(f"❌ {error_msg}")
            
            print(f"✅ Zakończono przemianowanie: {renamed_count} plików przemianowano")
            if errors:
                print(f"⚠️ Wystąpiły błędy: {len(errors)}")
                for error in errors:
                    print(f"   - {error}")
            
            return {
                "renamed": renamed_count,
                "errors": errors,
                "renamed_files": renamed_files,
                "message": f"Przemianowano {renamed_count} plików"
            }
            
        except Exception as e:
            error_msg = f"Błąd podczas przemianowania: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return {
                "renamed": renamed_count,
                "errors": errors,
                "renamed_files": renamed_files,
                "message": f"Błąd: {error_msg}"
            } 