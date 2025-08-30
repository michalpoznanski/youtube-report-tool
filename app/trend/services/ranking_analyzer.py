import json
import pandas as pd
from datetime import date, timedelta
import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RankingAnalyzer:
    def __init__(self, base_path_str: str = None):
        from app.config.settings import settings
        self.base_path = Path(base_path_str) if base_path_str else settings.reports_path
        self.base_path.mkdir(exist_ok=True)
        print(f"✅ RankingAnalyzer zainicjalizowany z ścieżką: {self.base_path}")

    def run_analysis_for_category(self, category: str) -> bool:
        """
        Implementuje prawdziwą logikę 5-dniowego okna śledzenia:
        1. Wczytuje CSV (dzisiejsze dane) + JSON (wczorajszy ranking)
        2. Łączy i aktualizuje dane
        3. Tworzy Top 10 z połączonych danych
        4. Zapisuje stan na jutro
        """
        try:
            today = date.today()
            print(f"🔄 Rozpoczynam analizę rankingu dla kategorii: {category}")
            
            # 1. WCZYTAJ DANE - znajdź najnowszy dostępny raport CSV
            pattern = f"report_{category.upper()}_*.csv"
            csv_files = list(self.base_path.glob(pattern))
            
            if not csv_files:
                print(f"⚠️ Nie znaleziono żadnych raportów CSV dla {category}. Pomijam analizę.")
                logger.warning(f"Nie znaleziono raportów CSV dla {category}")
                return False
            
            # Weź najnowszy raport CSV
            latest_csv_path = sorted(csv_files)[-1]
            latest_date_str = latest_csv_path.stem.split('_')[-1]
            latest_date_obj = datetime.datetime.strptime(latest_date_str, '%Y-%m-%d').date()
            
            print(f"📊 Używam najnowszego dostępnego raportu CSV: {latest_csv_path}")
            print(f"📅 Data raportu CSV: {latest_date_str}")
            
            # 2. WCZYTAJ WCZORAJSZY RANKING JSON (plik-pamięć)
            yesterday_ranking_path = self.base_path / f"ranking_{category.upper()}_{latest_date_obj - timedelta(days=1)}.json"
            
            print(f"📁 Szukam wczorajszego rankingu: {yesterday_ranking_path}")
            
            # Wczytaj dane CSV
            print(f"📊 Wczytuję raport CSV: {latest_csv_path}")
            df_csv = pd.read_csv(latest_csv_path)
            print(f"✅ Wczytano {len(df_csv)} filmów z CSV")
            
            # Wczytaj wczorajszy ranking (jeśli istnieje)
            yesterday_data = {"shorts": [], "longform": []}
            has_yesterday_data = False
            if yesterday_ranking_path.exists():
                print(f"📁 Znaleziono wczorajszy ranking: {yesterday_ranking_path}")
                try:
                    with open(yesterday_ranking_path, 'r', encoding='utf-8') as f:
                        yesterday_data = json.load(f)
                    print(f"📊 Wczytano wczorajszy ranking: {len(yesterday_data.get('shorts', []))} shorts, {len(yesterday_data.get('longform', []))} longform")
                    has_yesterday_data = True
                except Exception as e:
                    print(f"⚠️ Błąd podczas wczytywania wczorajszego rankingu: {e}")
                    yesterday_data = {"shorts": [], "longform": []}
                    has_yesterday_data = False
            else:
                print(f"⚠️ Brak wczorajszego rankingu - to pierwsza analiza")
                has_yesterday_data = False
            
            # 3. POŁĄCZ I ZAKTUALIZUJ DANE
            if has_yesterday_data:
                print("🔄 Łączę dane z CSV i wczorajszego rankingu...")
                
                # Konwertuj CSV na format słownika
                csv_videos = []
                for _, row in df_csv.iterrows():
                    video = {
                        'video_id': str(row.get('Video_ID', '')),
                        'title': str(row.get('Title', '')),
                        'channel': str(row.get('Channel_Name', '')),
                        'views': int(row.get('View_Count', 0)),
                        'thumbnail_url': str(row.get('Thumbnail_URL', '')),
                        'published_date': str(row.get('Date_of_Publishing', '')),
                        'source': 'csv',
                        'date': latest_date_str
                    }
                    csv_videos.append(video)
                
                # Konwertuj wczorajszy ranking na format słownika
                yesterday_videos = []
                for video_type in ['shorts', 'longform']:
                    for video in yesterday_data.get(video_type, []):
                        video_copy = video.copy()
                        video_copy['source'] = 'yesterday'
                        video_copy['date'] = str(latest_date_obj - timedelta(days=1))
                        yesterday_videos.append(video_copy)
                
                # 4. POŁĄCZ DANE - CSV ma priorytet (nowsze dane)
                print("🔄 Łączę dane z priorytetem dla CSV...")
                
                combined_videos = {}
                
                # Najpierw dodaj wczorajsze dane
                for video in yesterday_videos:
                    video_id = video['video_id']
                    if video_id:
                        combined_videos[video_id] = video
                
                # Następnie dodaj/aktualizuj danymi z CSV (mają priorytet)
                for video in csv_videos:
                    video_id = video['video_id']
                    if video_id:
                        if video_id in combined_videos:
                            # Aktualizuj istniejący film nowszymi danymi z CSV
                            old_video = combined_videos[video_id]
                            old_views = old_video.get('views', 0)
                            combined_videos[video_id] = {
                                **old_video,
                                'views': video['views'],  # Nowe wyświetlenia z CSV
                                'title': video['title'],   # Nowy tytuł z CSV
                                'channel': video['channel'], # Nowy kanał z CSV
                                'thumbnail_url': video['thumbnail_url'], # Nowa miniatura z CSV
                                'published_date': video['published_date'], # Nowa data z CSV
                                'source': 'csv_updated',
                                'date': latest_date_str,
                                'previous_views': old_views  # Zachowaj poprzednie wyświetlenia
                            }
                            print(f"🔄 Zaktualizowano film: {video['title'][:50]}... (wyświetlenia: {old_views} → {video['views']})")
                        else:
                            # Nowy film z CSV
                            combined_videos[video_id] = video
                            print(f"🆕 Dodano nowy film: {video['title'][:50]}...")
                
                print(f"✅ Połączono {len(combined_videos)} unikalnych filmów")
                
            else:
                print("🔄 To pierwsza analiza - używam tylko danych z CSV...")
                
                # Konwertuj CSV na format słownika
                csv_videos = []
                for _, row in df_csv.iterrows():
                    video = {
                        'video_id': str(row.get('Video_ID', '')),
                        'title': str(row.get('Title', '')),
                        'channel': str(row.get('Channel_Name', '')),
                        'views': int(row.get('View_Count', 0)),
                        'thumbnail_url': str(row.get('Thumbnail_URL', '')),
                        'published_date': str(row.get('Date_of_Publishing', '')),
                        'source': 'csv',
                        'date': latest_date_str
                    }
                    csv_videos.append(video)
                
                combined_videos = {video['video_id']: video for video in csv_videos if video['video_id']}
                print(f"✅ Używam {len(combined_videos)} filmów z CSV (pierwsza analiza)")
            
            # 5. PODZIEL NA SHORTS I LONG-FORM
            print("🔄 Dzielę filmy na kategorie...")
            
            shorts_videos = []
            longform_videos = []
            
            for video in combined_videos.values():
                # Użyj logiki z CSV do określenia typu
                if video['source'] == 'csv' or video['source'] == 'csv_updated':
                    # Sprawdź w oryginalnym CSV
                    csv_row = df_csv[df_csv['Video_ID'] == video['video_id']]
                    if not csv_row.empty:
                        video_type = csv_row.iloc[0].get('Video_Type', 'longform')
                        if video_type == 'shorts':
                            shorts_videos.append(video)
                        else:
                            longform_videos.append(video)
                    else:
                        # Fallback - dodaj do longform
                        longform_videos.append(video)
                else:
                    # Film z wczorajszego rankingu - zachowaj oryginalny typ
                    if 'video_type' in video:
                        if video['video_type'] == 'shorts':
                            shorts_videos.append(video)
                        else:
                            longform_videos.append(video)
                    else:
                        # Fallback - dodaj do longform
                        longform_videos.append(video)
            
            print(f"📱 Shorts: {len(shorts_videos)} filmów")
            print(f"🎬 Long-form: {len(longform_videos)} filmów")
            
            # 6. POSORTUJ I WYBIERZ TOP 10 (OPCJA A - po wyświetleniach)
            print("🏆 Sortuję i wybieram Top 10...")
            
            # Sortuj po wyświetleniach (malejąco)
            shorts_sorted = sorted(shorts_videos, key=lambda x: x['views'], reverse=True)
            longform_sorted = sorted(longform_videos, key=lambda x: x['views'], reverse=True)
            
            # Wybierz Top 10
            top_10_shorts = shorts_sorted[:10]
            top_10_longform = longform_sorted[:10]
            
            print(f"🏆 Top 10 Shorts: {len(top_10_shorts)} filmów")
            print(f"🏆 Top 10 Long-form: {len(top_10_longform)} filmów")
            
            # 7. KONWERTUJ DO FORMATU STAREGO SYSTEMU (z trendami)
            print("🔄 Konwertuję dane do formatu starego systemu...")
            
            def convert_to_old_format(videos_list, video_type):
                """Konwertuje dane do formatu starego systemu z trendami"""
                converted = []
                for i, video in enumerate(videos_list):
                    # Oblicz trend na podstawie pozycji i źródła danych
                    if video['source'] == 'csv' or video['source'] == 'csv_updated':
                        if i == 0:
                            trend = 'new'  # Pierwszy = nowy
                        elif i < 3:
                            trend = 'up'   # Top 3 = w górę
                        else:
                            trend = 'stable'  # Reszta = stabilne
                    else:
                        # Film z wczorajszego rankingu
                        trend = 'stable'
                    
                    converted_video = {
                        'video_id': video.get('video_id', ''),
                        'title': video.get('title', ''),
                        'channel': video.get('channel', ''),
                        'views': video.get('views', 0),
                        'trend': trend,
                        'thumbnail_url': video.get('thumbnail_url', ''),
                        'published_date': video.get('published_date', ''),
                        'video_type': video_type,
                        'source': video.get('source', ''),
                        'date': video.get('date', ''),
                        'previous_views': video.get('previous_views', None)
                    }
                    converted.append(converted_video)
                return converted
            
            # Konwertuj rankingi
            shorts_formatted = convert_to_old_format(top_10_shorts, 'shorts')
            longform_formatted = convert_to_old_format(top_10_longform, 'longform')
            
            # Przygotuj historię pozycji (dla kompatybilności)
            history = {}
            for video in shorts_formatted + longform_formatted:
                history[video['video_id']] = {
                    'current_position': shorts_formatted.index(video) + 1 if video in shorts_formatted else longform_formatted.index(video) + 1,
                    'previous_position': None,  # Będzie dostępne w następnej analizie
                    'trend': video['trend'],
                    'source': video.get('source', ''),
                    'last_updated': video.get('date', ''),
                    'views_change': video.get('previous_views') - video.get('views') if video.get('previous_views') else None
                }
            
            # 8. ZAPISZ STAN NA JUTRO (plik-pamięć)
            print("💾 Zapisuję ranking na jutro...")
            final_ranking = {
                'shorts': shorts_formatted,
                'longform': longform_formatted,
                'history': history,
                'last_updated': today.isoformat(),
                'analysis_date': today.isoformat(),
                'csv_date': latest_date_str,
                'yesterday_ranking_date': str(latest_date_obj - timedelta(days=1)) if yesterday_ranking_path.exists() else None,
                'total_videos_analyzed': len(combined_videos),
                'shorts_count': len(shorts_videos),
                'longform_count': len(longform_videos),
                'csv_videos_count': len(csv_videos),
                'yesterday_videos_count': len(yesterday_videos) if has_yesterday_data else 0,
                'combined_videos_count': len(combined_videos),
                'analysis_method': 'csv_plus_yesterday_ranking' if has_yesterday_data else 'csv_only_first_run',
                'views_updated_from_csv': len([v for v in combined_videos.values() if v.get('source') == 'csv_updated']) if has_yesterday_data else 0,
                'has_yesterday_data': has_yesterday_data,
                'csv_file_used': latest_csv_path.name
            }
            
            output_path = self.base_path / f"ranking_{category.upper()}_{today}.json"
            print(f"📁 Zapisuję ranking do: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_ranking, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Zapisano analizę rankingu dla {category.upper()} w pliku: {output_path}")
            print(f"📊 Statystyki:")
            print(f"   - CSV: {len(csv_videos)} filmów")
            if has_yesterday_data:
                print(f"   - Wczorajszy ranking: {len(yesterday_videos)} filmów")
                print(f"   - Połączone: {len(combined_videos)} filmów")
                print(f"   - Zaktualizowane wyświetlenia: {len([v for v in combined_videos.values() if v.get('source') == 'csv_updated'])}")
            else:
                print(f"   - Pierwsza analiza: {len(combined_videos)} filmów z CSV")
            print(f"   - Top 10 Shorts: {len(top_10_shorts)} filmów")
            print(f"   - Top 10 Long-form: {len(top_10_longform)} filmów")
            print(f"   - Metoda analizy: {'CSV + wczorajszy ranking' if has_yesterday_data else 'Tylko CSV (pierwsza analiza)'}")
            
            logger.info(f"Pomyślnie wygenerowano ranking dla {category}: {len(top_10_shorts)} shorts, {len(top_10_longform)} longform")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas analizy rankingu dla {category}: {e}")
            logger.error(f"Błąd podczas analizy rankingu dla {category}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_latest_ranking(self, category: str) -> Dict[str, Any]:
        """
        Pobiera najnowszy ranking dla danej kategorii.
        
        Args:
            category (str): Nazwa kategorii
            
        Returns:
            Dict[str, Any]: Ranking lub pusty słownik jeśli nie istnieje
        """
        try:
            today = date.today()
            ranking_path = self.base_path / f"ranking_{category.upper()}_{today}.json"
            
            if ranking_path.exists():
                with open(ranking_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"ℹ️ Brak rankingu dla {category} z dzisiaj: {ranking_path}")
                return {"shorts": [], "longform": [], "error": "Brak rankingu"}
                
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania rankingu dla {category}: {e}")
            logger.error(f"Błąd podczas wczytywania rankingu dla {category}: {e}")
            return {"shorts": [], "longform": [], "error": str(e)}
