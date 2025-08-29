import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RankingManager:
    """
    Zarządza rankingami top 10 filmów dla każdej kategorii.
    Śledzi filmy przez maksymalnie 10 dni, pokazując wzloty i upadki.
    """
    
    def __init__(self):
        # Użyj Railway Volume Path zamiast lokalnego katalogu
        from app.config.settings import settings
        self.rankings_dir = settings.data_path / "rankings"
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
        
    def get_ranking_file_path(self, category: str) -> Path:
        """Zwraca ścieżkę do pliku rankingu dla danej kategorii"""
        return self.rankings_dir / f"ranking_{category.upper()}.json"
    
    def load_ranking(self, category: str) -> Dict:
        """Ładuje ranking dla danej kategorii"""
        ranking_file = self.get_ranking_file_path(category)
        
        if not ranking_file.exists():
            logger.info(f"Ranking dla kategorii {category} nie istnieje - generuję automatycznie")
            # Automatycznie wygeneruj ranking jeśli nie istnieje
            try:
                from app.trend.services.csv_processor import get_trend_data
                from datetime import date
                
                # Pobierz najnowsze dane CSV
                videos = get_trend_data(category=category, report_date=date.today())
                
                if videos:
                    # Wygeneruj ranking
                    ranking_data = self.update_ranking(category, videos)
                    logger.info(f"Automatycznie wygenerowano ranking dla kategorii {category}")
                    return ranking_data
                else:
                    logger.warning(f"Brak danych CSV dla kategorii {category} - nie można wygenerować rankingu")
            except Exception as e:
                logger.error(f"Błąd podczas automatycznego generowania rankingu dla {category}: {e}")
            
            # Zwróć pusty ranking jeśli nie udało się wygenerować
            return {
                "category": category,
                "last_updated": None,
                "shorts": [],
                "longform": [],
                "history": {}
            }
        
        try:
            with open(ranking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Błąd podczas ładowania rankingu dla {category}: {e}")
            return {
                "category": category,
                "last_updated": None,
                "shorts": [],
                "longform": [],
                "history": {}
            }
    
    def save_ranking(self, category: str, ranking_data: Dict):
        """Zapisuje ranking dla danej kategorii"""
        ranking_file = self.get_ranking_file_path(category)
        
        try:
            with open(ranking_file, 'w', encoding='utf-8') as f:
                json.dump(ranking_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Zapisano ranking dla kategorii {category}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania rankingu dla {category}: {e}")
    
    def determine_video_type(self, duration: str) -> str:
        """Określa typ filmu na podstawie długości"""
        try:
            if pd.isna(duration):
                return "Longform"
            
            # Sprawdź czy to format ISO 8601 (PT1H2M3S)
            if isinstance(duration, str) and duration.startswith('PT'):
                # Parsuj format PT1H2M3S
                hours = 0
                minutes = 0
                seconds = 0
                
                if 'H' in duration:
                    hours = int(duration.split('H')[0].split('T')[1])
                if 'M' in duration:
                    minutes = int(duration.split('M')[0].split('T')[-1])
                if 'S' in duration:
                    seconds = int(duration.split('S')[0].split('T')[-1])
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                # Filmy do 10 minut (600 sekund) to shorts, powyżej to long-form
                return "Shorts" if total_seconds <= 600 else "Longform"
            else:
                # Sprawdź czy to liczba sekund
                duration_seconds = int(duration)
                # Filmy do 10 minut (600 sekund) to shorts, powyżej to long-form
                return "Shorts" if duration_seconds <= 600 else "Longform"
                
        except (ValueError, TypeError):
            return "Longform"
    
    def update_ranking(self, category: str, videos: List[Dict]) -> Dict:
        """
        Aktualizuje ranking dla danej kategorii na podstawie nowych danych.
        
        Args:
            category: Nazwa kategorii
            videos: Lista filmów z CSV
            
        Returns:
            Zaktualizowany ranking
        """
        logger.info(f"Aktualizuję ranking dla kategorii {category}")
        
        # Załaduj obecny ranking
        current_ranking = self.load_ranking(category)
        
        # Użyj csv_processor do przetworzenia danych z poprawną logiką
        try:
            from app.trend.services.csv_processor import get_trend_data
            from datetime import date
            
            # Pobierz przetworzone dane przez csv_processor
            processed_videos = get_trend_data(category=category, report_date=date.today())
            
            if processed_videos:
                logger.info(f"Użyto csv_processor do przetworzenia {len(processed_videos)} filmów")
                
                # Użyj przetworzonych danych z csv_processor
                video_data = []
                for video in processed_videos:
                    try:
                        video_data.append({
                            'video_id': str(video.get('video_id', '')),
                            'title': str(video.get('title', '')),
                            'channel': str(video.get('channel', '')),
                            'views': int(video.get('views', 0)),
                            'video_type': str(video.get('video_type', 'Longform')),
                            'duration': str(video.get('duration', '')),
                            'thumbnail_url': str(video.get('thumbnail_url', ''))
                        })
                    except Exception as e:
                        logger.warning(f"Pominięto film z błędem: {e}")
                        continue
                
                logger.info(f"Przetworzono {len(video_data)} filmów przez csv_processor")
            else:
                logger.warning("csv_processor nie zwrócił danych, używam surowych danych CSV")
                # Fallback do starej logiki
                video_data = self._process_raw_csv_data(videos)
        except Exception as e:
            logger.warning(f"Błąd podczas używania csv_processor: {e}, używam surowych danych CSV")
            # Fallback do starej logiki
            video_data = self._process_raw_csv_data(videos)
        
        # Podziel na SHORTS i LONG FORM
        shorts = [v for v in video_data if v['video_type'] == 'Shorts']
        longform = [v for v in video_data if v['video_type'] == 'Longform']
        
        # Sortuj po wyświetleniach (malejąco)
        shorts.sort(key=lambda x: x['views'], reverse=True)
        longform.sort(key=lambda x: x['views'], reverse=True)
        
        # Weź top 10 dla każdego typu
        top_shorts = shorts[:10]
        top_longform = longform[:10]
        
        # Aktualizuj ranking
        new_ranking = {
            "category": category,
            "last_updated": datetime.now().isoformat(),
            "shorts": top_shorts,
            "longform": top_longform,
            "history": current_ranking.get("history", {})
        }
        
        # Aktualizuj historię pozycji
        self._update_position_history(new_ranking, current_ranking)
        
        # Oblicz trendy dla każdego filmu
        self._calculate_trends(new_ranking, current_ranking)
        
        # Usuń filmy starsze niż 10 dni
        self._cleanup_old_videos(new_ranking)
        
        # Zapisz nowy ranking
        self.save_ranking(category, new_ranking)
        
        logger.info(f"Zaktualizowano ranking dla {category}: {len(top_shorts)} shorts, {len(top_longform)} longform")
        return new_ranking
    
    def _update_position_history(self, new_ranking: Dict, old_ranking: Dict):
        """Aktualizuje historię pozycji filmów"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Aktualizuj historię dla SHORTS
        for i, video in enumerate(new_ranking["shorts"]):
            video_id = video['video_id']
            if video_id not in new_ranking["history"]:
                new_ranking["history"][video_id] = {
                    "title": video['title'],
                    "channel": video['channel'],
                    "positions": []
                }
            
            # Dodaj dzisiejszą pozycję
            new_ranking["history"][video_id]["positions"].append({
                "date": today,
                "position": i + 1,
                "views": video['views'],
                "type": "Shorts"
            })
        
        # Aktualizuj historię dla LONG FORM
        for i, video in enumerate(new_ranking["longform"]):
            video_id = video['video_id']
            if video_id not in new_ranking["history"]:
                new_ranking["history"][video_id] = {
                    "title": video['title'],
                    "channel": video['channel'],
                    "positions": []
                }
            
            # Dodaj dzisiejszą pozycję
            new_ranking["history"][video_id]["positions"].append({
                "date": today,
                "position": i + 1,
                "views": video['views'],
                "type": "Longform"
            })
    
    def _cleanup_old_videos(self, ranking: Dict):
        """Usuwa filmy starsze niż 10 dni z historii"""
        cutoff_date = datetime.now() - timedelta(days=10)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        # Usuń stare pozycje z historii
        for video_id in list(ranking["history"].keys()):
            ranking["history"][video_id]["positions"] = [
                pos for pos in ranking["history"][video_id]["positions"]
                if pos["date"] >= cutoff_str
            ]
            
            # Jeśli film nie ma pozycji w ostatnich 10 dniach, usuń go z historii
            if not ranking["history"][video_id]["positions"]:
                del ranking["history"][video_id]
    
    def clear_ranking(self, category: str):
        """Czyści ranking dla danej kategorii, wymuszając regenerację"""
        ranking_file = self.get_ranking_file_path(category)
        
        if ranking_file.exists():
            try:
                ranking_file.unlink()
                logger.info(f"Usunięto stary ranking dla kategorii {category}")
                return True
            except Exception as e:
                logger.error(f"Błąd podczas usuwania rankingu dla {category}: {e}")
                return False
        else:
            logger.info(f"Brak rankingu do usunięcia dla kategorii {category}")
            return True
    
    def get_ranking_summary(self, category: str) -> Dict:
        """Zwraca podsumowanie rankingu z wzlotami i upadkami"""
        ranking = self.load_ranking(category)
        
        if not ranking["last_updated"]:
            return {"error": "Brak danych rankingu"}
        
        summary = {
            "category": category,
            "last_updated": ranking["last_updated"],
            "shorts": {
                "count": len(ranking["shorts"]),
                "top_video": ranking["shorts"][0] if ranking["shorts"] else None
            },
            "longform": {
                "count": len(ranking["longform"]),
                "top_video": ranking["longform"][0] if ranking["longform"] else None
            },
            "trends": self._analyze_trends(ranking)
        }
        
        return summary
    
    def _analyze_trends(self, ranking: Dict) -> Dict:
        """Analizuje trendy w rankingu (wzloty i upadki)"""
        trends = {
            "rising_stars": [],
            "falling_stars": [],
            "stable_stars": []
        }
        
        for video_id, history in ranking["history"].items():
            if len(history["positions"]) < 2:
                continue
            
            # Porównaj ostatnie 2 pozycje
            current = history["positions"][-1]
            previous = history["positions"][-2]
            
            if current["position"] < previous["position"]:
                # Film awansował
                trends["rising_stars"].append({
                    "video_id": video_id,
                    "title": history["title"],
                    "channel": history["channel"],
                    "from_position": previous["position"],
                    "to_position": current["position"],
                    "views_change": current["views"] - previous["views"]
                })
            elif current["position"] > previous["position"]:
                # Film spadł
                trends["falling_stars"].append({
                    "video_id": video_id,
                    "title": history["title"],
                    "channel": history["channel"],
                    "from_position": previous["position"],
                    "to_position": current["position"],
                    "views_change": current["views"] - previous["views"]
                })
            else:
                # Film utrzymał pozycję
                trends["stable_stars"].append({
                    "video_id": video_id,
                    "title": history["title"],
                    "channel": history["channel"],
                    "position": current["position"],
                    "views": current["views"]
                })
        
        # Sortuj po zmianie pozycji
        trends["rising_stars"].sort(key=lambda x: x["from_position"] - x["to_position"], reverse=True)
        trends["falling_stars"].sort(key=lambda x: x["to_position"] - x["from_position"], reverse=True)
        
        return trends
    
    def _process_raw_csv_data(self, videos: List[Dict]) -> List[Dict]:
        """Przetwarza surowe dane CSV jako fallback"""
        logger.info("Używam fallback do przetwarzania surowych danych CSV")
        
        video_data = []
        
        # Określ format danych CSV
        is_new_format = any('Video_ID' in str(video.keys()) for video in videos[:5]) if videos else False
        
        for video in videos:
            try:
                # Debug: sprawdź co jest w video
                logger.debug(f"Przetwarzam film: {video.get('Title', video.get('title', 'Brak tytułu'))}")
                logger.debug(f"Video keys: {list(video.keys())}")
                
                # Mapuj kolumny na podstawie formatu
                if is_new_format:
                    # Nowy format: Video_ID, Title, View_Count, Duration, Channel_Name
                    video_id = video.get('Video_ID', '')
                    title = video.get('Title', '')
                    view_count = video.get('View_Count', 0)
                    duration = video.get('Duration', '')
                    channel = video.get('Channel_Name', '')
                else:
                    # Stary format: video_id, title, views_today, duration_seconds, channel
                    video_id = video.get('video_id', '')
                    title = video.get('title', '')
                    view_count = video.get('views_today', 0)
                    duration = video.get('duration_seconds', '')
                    channel = video.get('channel', '')
                
                # Określ typ filmu
                video_type = self.determine_video_type(duration)
                
                # Pobierz liczbę wyświetleń
                if isinstance(view_count, str):
                    view_count = int(view_count.replace(',', ''))
                
                video_data.append({
                    'video_id': str(video_id),
                    'title': str(title),
                    'channel': str(channel),
                    'views': int(view_count),
                    'video_type': video_type,
                    'duration': str(duration),
                    'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                })
            except Exception as e:
                logger.warning(f"Pominięto film z błędem: {e}")
                continue
        
        return video_data
    
    def _calculate_trends(self, new_ranking: Dict, old_ranking: Dict):
        """Oblicza trendy dla każdego filmu (wzloty/spadki)"""
        if not old_ranking.get("shorts") and not old_ranking.get("longform"):
            # Brak poprzedniego rankingu, nie można obliczyć trendów
            return
        
        # Oblicz trendy dla SHORTS
        for video in new_ranking["shorts"]:
            video_id = video['video_id']
            old_position = self._find_old_position(video_id, old_ranking, "shorts")
            if old_position:
                video['trend'] = self._determine_trend(old_position, video['views'])
            else:
                video['trend'] = 'new'  # Nowy film
        
        # Oblicz trendy dla LONG FORM
        for video in new_ranking["longform"]:
            video_id = video['video_id']
            old_position = self._find_old_position(video_id, old_ranking, "longform")
            if old_position:
                video['trend'] = self._determine_trend(old_position, video['views'])
            else:
                video['trend'] = 'new'  # Nowy film
    
    def _find_old_position(self, video_id: str, old_ranking: Dict, category: str) -> Dict:
        """Znajduje poprzednią pozycję filmu w rankingu"""
        if not old_ranking.get(category):
            return None
        
        for i, video in enumerate(old_ranking[category]):
            if video.get('video_id') == video_id:
                return {
                    'position': i + 1,
                    'views': video.get('views', 0)
                }
        return None
    
    def _determine_trend(self, old_data: Dict, new_views: int) -> str:
        """Określa trend filmu na podstawie zmiany pozycji i wyświetleń"""
        old_position = old_data['position']
        old_views = old_data['views']
        
        # Oblicz zmianę wyświetleń
        views_change = new_views - old_views
        
        if views_change > 0:
            return 'up'  # Film rośnie
        elif views_change < 0:
            return 'down'  # Film maleje
        else:
            return 'stable'  # Film stabilny


# Instancja globalna
ranking_manager = RankingManager()
