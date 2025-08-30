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
        Implementuje prawdziwą logikę analizy rankingowej:
        1. Wczytuje KILKA najnowszych raportów CSV (ostatnie 3-5 dni)
        2. Łączy wszystkie dane w jedną bazę
        3. Tworzy Top 10 z połączonych danych
        4. Zapisuje stan na jutro
        """
        try:
            today = date.today()
            print(f"🔄 Rozpoczynam analizę rankingu dla kategorii: {category}")
            
            # 1. WCZYTAJ KILKA NAJNOWSZYCH RAPORTÓW CSV (ostatnie 5 dni)
            pattern = f"report_{category.upper()}_*.csv"
            csv_files = list(self.base_path.glob(pattern))
            
            if not csv_files:
                print(f"⚠️ Nie znaleziono żadnych raportów CSV dla {category}. Pomijam analizę.")
                logger.warning(f"Nie znaleziono raportów CSV dla {category}")
                return False
            
            # Sortuj pliki po dacie (najnowsze na końcu)
            csv_files_sorted = sorted(csv_files, key=lambda x: x.stem.split('_')[-1])
            
            # Weź ostatnie 5 raportów (lub wszystkie jeśli mniej niż 5)
            recent_csv_files = csv_files_sorted[-5:] if len(csv_files_sorted) >= 5 else csv_files_sorted
            
            print(f"📊 Znaleziono {len(csv_files)} raportów CSV dla {category}")
            print(f"📊 Używam {len(recent_csv_files)} najnowszych raportów:")
            for csv_file in recent_csv_files:
                date_str = csv_file.stem.split('_')[-1]
                print(f"   - {csv_file.name} (data: {date_str})")
            
            # 2. WCZYTAJ I POŁĄCZ WSZYSTKIE DANE Z CSV
            print("🔄 Wczytuję i łączę dane z wszystkich raportów CSV...")
            
            all_videos = {}  # Słownik: video_id -> najnowsze dane
            
            for csv_file in recent_csv_files:
                date_str = csv_file.stem.split('_')[-1]
                print(f"📊 Wczytuję raport: {csv_file.name}")
                
                try:
                    df = pd.read_csv(csv_file)
                    print(f"   ✅ Wczytano {len(df)} filmów z {date_str}")
                    
                    # Przetwórz każdy film z tego raportu
                    for _, row in df.iterrows():
                        video_id = str(row.get('Video_ID', ''))
                        if not video_id:
                            continue
                        
                        video_data = {
                            'video_id': video_id,
                            'title': str(row.get('Title', '')),
                            'channel': str(row.get('Channel_Name', '')),
                            'views': int(row.get('View_Count', 0)),
                            'thumbnail_url': str(row.get('Thumbnail_URL', '')),
                            'published_date': str(row.get('Date_of_Publishing', '')),
                            'video_type': str(row.get('Video_Type', 'longform')),
                            'source_date': date_str,
                            'report_file': csv_file.name
                        }
                        
                        # Jeśli film już istnieje, zaktualizuj danymi z nowszego raportu
                        if video_id in all_videos:
                            existing_video = all_videos[video_id]
                            existing_date = datetime.datetime.strptime(existing_video['source_date'], '%Y-%m-%d').date()
                            new_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                            
                            if new_date > existing_date:
                                # Nowszy raport - aktualizuj dane
                                old_views = existing_video['views']
                                all_videos[video_id] = video_data
                                print(f"   🔄 Zaktualizowano film: {video_data['title'][:50]}... (wyświetlenia: {old_views} → {video_data['views']})")
                            # Jeśli starszy raport - pomiń
                        else:
                            # Nowy film - dodaj
                            all_videos[video_id] = video_data
                            print(f"   🆕 Dodano nowy film: {video_data['title'][:50]}...")
                
                except Exception as e:
                    print(f"   ❌ Błąd podczas wczytywania {csv_file.name}: {e}")
                    continue
            
            print(f"✅ Połączono dane z {len(recent_csv_files)} raportów: {len(all_videos)} unikalnych filmów")
            
            # Sprawdź czy Marcin Banot jest w danych
            marcin_banot_found = False
            for video in all_videos.values():
                if 'Marcin Banot' in video['title'] or 'Cyprian Majcher' in video['channel']:
                    print(f"🎯 ZNALEZIONO: {video['title']} - {video['channel']} - {video['views']} wyświetleń z {video['source_date']}")
                    marcin_banot_found = True
            
            if not marcin_banot_found:
                print(f"⚠️ NIE ZNALEZIONO filmu Marcin Banot w danych!")
            else:
                print(f"✅ ZNALEZIONO film Marcin Banot w danych!")
            
            # 3. PODZIEL NA SHORTS I LONG-FORM
            print("🔄 Dzielę filmy na kategorie...")
            
            shorts_videos = []
            longform_videos = []
            
            for video in all_videos.values():
                if video['video_type'].lower() == 'shorts':
                    shorts_videos.append(video)
                else:
                    longform_videos.append(video)
            
            print(f"📱 Shorts: {len(shorts_videos)} filmów")
            print(f"🎬 Long-form: {len(longform_videos)} filmów")
            
            # 4. POSORTUJ I WYBIERZ TOP 10 (OPCJA A - po wyświetleniach)
            print("🏆 Sortuję i wybieram Top 10...")
            
            # Sortuj po wyświetleniach (malejąco)
            shorts_sorted = sorted(shorts_videos, key=lambda x: x['views'], reverse=True)
            longform_sorted = sorted(longform_videos, key=lambda x: x['views'], reverse=True)
            
            # Wybierz Top 10
            top_10_shorts = shorts_sorted[:10]
            top_10_longform = longform_sorted[:10]
            
            print(f"🏆 Top 10 Shorts: {len(top_10_shorts)} filmów")
            print(f"🏆 Top 10 Long-form: {len(top_10_longform)} filmów")
            
            # 5. KONWERTUJ DO FORMATU STAREGO SYSTEMU (z trendami)
            print("🔄 Konwertuję dane do formatu starego systemu...")
            
            def convert_to_old_format(videos_list, video_type):
                """Konwertuje dane do formatu starego systemu z trendami"""
                converted = []
                for i, video in enumerate(videos_list):
                    # Oblicz trend na podstawie pozycji
                    if i == 0:
                        trend = 'new'  # Pierwszy = nowy
                    elif i < 3:
                        trend = 'up'   # Top 3 = w górę
                    else:
                        trend = 'stable'  # Reszta = stabilne
                    
                    converted_video = {
                        'video_id': video.get('video_id', ''),
                        'title': video.get('title', ''),
                        'channel': video.get('channel', ''),
                        'views': video.get('views', 0),
                        'trend': trend,
                        'thumbnail_url': video.get('thumbnail_url', ''),
                        'published_date': video.get('published_date', ''),
                        'video_type': video_type,
                        'source_date': video.get('source_date', ''),
                        'report_file': video.get('report_file', '')
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
                    'source_date': video.get('source_date', ''),
                    'report_file': video.get('report_file', '')
                }
            
            # 6. ZAPISZ STAN NA JUTRO (plik-pamięć)
            print("💾 Zapisuję ranking na jutro...")
            
            # Znajdź najnowszą datę z użytych raportów
            latest_report_date = max([video['source_date'] for video in all_videos.values()])
            
            final_ranking = {
                'shorts': shorts_formatted,
                'longform': longform_formatted,
                'history': history,
                'last_updated': today.isoformat(),
                'analysis_date': today.isoformat(),
                'latest_csv_date': latest_report_date,
                'csv_files_used': [f.name for f in recent_csv_files],
                'total_videos_analyzed': len(all_videos),
                'shorts_count': len(shorts_videos),
                'longform_count': len(longform_videos),
                'csv_reports_count': len(recent_csv_files),
                'analysis_method': 'multiple_csv_analysis',
                'date_range': f"{min([video['source_date'] for video in all_videos.values()])} - {latest_report_date}"
            }
            
            output_path = self.base_path / f"ranking_{category.upper()}_{today}.json"
            print(f"📁 Zapisuję ranking do: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_ranking, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Zapisano analizę rankingu dla {category.upper()} w pliku: {output_path}")
            print(f"📊 Statystyki:")
            print(f"   - Użyte raporty CSV: {len(recent_csv_files)}")
            print(f"   - Zakres dat: {min([video['source_date'] for video in all_videos.values()])} - {latest_report_date}")
            print(f"   - Unikalne filmy: {len(all_videos)}")
            print(f"   - Top 10 Shorts: {len(top_10_shorts)} filmów")
            print(f"   - Top 10 Long-form: {len(top_10_longform)} filmów")
            print(f"   - Metoda analizy: Analiza z {len(recent_csv_files)} raportów CSV")
            
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
