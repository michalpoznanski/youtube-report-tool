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
        self.rankings_dir = Path("data/rankings")
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
        
    def get_ranking_file_path(self, category: str) -> Path:
        """Zwraca ścieżkę do pliku rankingu dla danej kategorii"""
        return self.rankings_dir / f"ranking_{category.upper()}.json"
    
    def load_ranking(self, category: str) -> Dict:
        """Ładuje ranking dla danej kategorii"""
        ranking_file = self.get_ranking_file_path(category)
        
        if not ranking_file.exists():
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
                return "Shorts" if total_seconds <= 60 else "Longform"
            else:
                # Sprawdź czy to liczba sekund
                duration_seconds = int(duration)
                return "Shorts" if duration_seconds <= 60 else "Longform"
                
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
        
        # Przygotuj dane do analizy
        video_data = []
        for video in videos:
            try:
                # Debug: sprawdź co jest w video
                logger.debug(f"Przetwarzam film: {video.get('Title', 'Brak tytułu')}")
                logger.debug(f"Video keys: {list(video.keys())}")
                logger.debug(f"View_Count: {video.get('View_Count', 'BRAK')}")
                logger.debug(f"Video_ID: {video.get('Video_ID', 'BRAK')}")
                logger.debug(f"Channel_Name: {video.get('Channel_Name', 'BRAK')}")
                
                # Określ typ filmu
                video_type = self.determine_video_type(video.get('Duration', video.get('duration_seconds', '')))
                
                # Pobierz liczbę wyświetleń
                view_count = video.get('View_Count', video.get('views_today', 0))
                if isinstance(view_count, str):
                    view_count = int(view_count.replace(',', ''))
                
                video_data.append({
                    'video_id': video.get('Video_ID', video.get('video_id', '')),
                    'title': video.get('Title', video.get('title', '')),
                    'channel': video.get('Channel_Name', video.get('channel', '')),
                    'views': int(view_count),
                    'video_type': video_type,
                    'duration': video.get('Duration', video.get('duration_seconds', '')),
                    'thumbnail_url': f"https://img.youtube.com/vi/{video.get('Video_ID', video.get('video_id', ''))}/mqdefault.jpg"
                })
            except Exception as e:
                logger.warning(f"Pominięto film z błędem: {e}")
                continue
        
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


# Instancja globalna
ranking_manager = RankingManager()
