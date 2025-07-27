#!/usr/bin/env python3
"""
SYSTEM ANALIZY NAZWISK - WARSZTAT
=================================

Analiza offline danych z raw_data/ bez zużywania quota
- Ładuje dane z ostatnich N dni
- Ekstrahuje nazwiska/słowa kluczowe
- Śledzi trendy dzień po dzień
- Generuje raporty wzrostu/spadku

AUTOR: Hook Boost V2 - Trend Analysis
WERSJA: Workshop Edition
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class AnalysisNameWorkshop:
    """System analizy nazwisk - WARSZTAT EDITION"""
    
    def __init__(self):
        self.raw_data_dir = "../raw_data"
        self.analysis_cache_dir = "../analysis_cache"
        
        # Tworzenie katalogów
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.analysis_cache_dir, exist_ok=True)
        
        # DEMO słowa kluczowe do śledzenia (na start)
        self.tracked_keywords = [
            # Polityka
            'tusk', 'donald tusk', 'kaczyński', 'jarosław kaczyński',
            'duda', 'andrzej duda', 'morawiecki', 'mateusz morawiecki',
            'trzaskowski', 'rafał trzaskowski', 'ziobro', 'zbigniew ziobro',
            'mentzen', 'sławomir mentzen', 'hołownia', 'szymon hołownia',
            
            # Showbiz
            'rozenek', 'małgorzata rozenek', 'wojewódzki', 'kuba wojewódzki',
            'dowbor', 'katarzyna dowbor', 'krupa', 'joanna krupa',
            'górniak', 'edyta górniak', 'martyniuk', 'zenon martyniuk',
            
            # Motoryzacja
            'maserati', 'ferrari', 'lamborghini', 'porsche', 'bmw',
            'test drive', 'jazda próbna', 'spalanie'
        ]
        
        print("🔍 SYSTEM ANALIZY NAZWISK GOTOWY")
        print(f"📁 Raw data: {self.raw_data_dir}")
        print(f"💾 Cache: {self.analysis_cache_dir}")
        print(f"🏷️ Śledzone słowa: {len(self.tracked_keywords)}")

    def get_available_days(self, room: str) -> List[str]:
        """Pobiera dostępne dni z raw_data dla danego pokoju"""
        pattern = f"raw_raport_*_{room}.json"
        files = []
        
        for file in os.listdir(self.raw_data_dir):
            if file.startswith("raw_raport_") and file.endswith(f"_{room}.json"):
                # Wyciągnij datę z nazwy pliku
                try:
                    date_part = file.replace("raw_raport_", "").replace(f"_{room}.json", "")
                    # Sprawdź czy to poprawny format daty YYYY-MM-DD
                    datetime.strptime(date_part, "%Y-%m-%d")
                    files.append(date_part)
                except ValueError:
                    continue
        
        return sorted(files, reverse=True)  # Najnowsze pierwsze

    def load_day_data(self, room: str, date: str) -> Optional[Dict]:
        """Ładuje dane z konkretnego dnia"""
        filename = f"raw_raport_{date}_{room}.json"
        filepath = os.path.join(self.raw_data_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Brak danych dla {date} ({room})")
            return None
        except Exception as e:
            print(f"❌ Błąd ładowania {filepath}: {e}")
            return None

    def extract_keywords_from_text(self, text: str) -> Dict[str, int]:
        """Ekstrahuje słowa kluczowe z tekstu i zlicza wystąpienia"""
        if not text:
            return {}
        
        text_lower = text.lower()
        keyword_counts = {}
        
        for keyword in self.tracked_keywords:
            keyword_lower = keyword.lower()
            # Zlicz wystąpienia
            count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text_lower))
            if count > 0:
                keyword_counts[keyword] = count
        
        return keyword_counts

    def analyze_video(self, video_data: Dict) -> Dict[str, int]:
        """Analizuje pojedynczy film i zwraca znalezione słowa kluczowe"""
        all_keywords = {}
        
        # Analizuj tytuł
        title_keywords = self.extract_keywords_from_text(video_data.get('title', ''))
        for kw, count in title_keywords.items():
            all_keywords[kw] = all_keywords.get(kw, 0) + count
        
        # Analizuj opis (jeśli dostępny)
        desc_keywords = self.extract_keywords_from_text(video_data.get('description', ''))
        for kw, count in desc_keywords.items():
            all_keywords[kw] = all_keywords.get(kw, 0) + count
        
        return all_keywords

    def analyze_day(self, room: str, date: str) -> Dict:
        """Analizuje dane z jednego dnia"""
        day_data = self.load_day_data(room, date)
        if not day_data:
            return {'date': date, 'keywords': {}, 'total_videos': 0, 'error': 'No data'}
        
        videos = day_data.get('videos', [])
        daily_keywords = defaultdict(lambda: {'count': 0, 'views': 0, 'videos': 0})
        
        for video in videos:
            video_keywords = self.analyze_video(video)
            views = int(video.get('view_count', 0))
            
            for keyword, count in video_keywords.items():
                daily_keywords[keyword]['count'] += count
                daily_keywords[keyword]['views'] += views
                daily_keywords[keyword]['videos'] += 1
        
        return {
            'date': date,
            'keywords': dict(daily_keywords),
            'total_videos': len(videos),
            'success': True
        }

    def analyze_names(self, room: str, days: int = 7) -> Dict:
        """Główna funkcja analizy nazwisk z N ostatnich dni"""
        print(f"🔍 ANALIZA NAZWISK: {room} ({days} dni)")
        print("=" * 50)
        
        # Pobierz dostępne dni
        available_days = self.get_available_days(room)
        
        if not available_days:
            return {
                'success': False,
                'error': f'Brak danych raw_data dla pokoju: {room}',
                'room': room,
                'requested_days': days
            }
        
        # Ogranicz do żądanej liczby dni
        analysis_days = available_days[:days]
        
        print(f"📅 Dostępne dni: {len(available_days)}")
        print(f"📊 Analizuję: {len(analysis_days)} dni")
        
        # Analizuj każdy dzień
        daily_results = []
        for date in analysis_days:
            print(f"🔄 Analizuję {date}...")
            day_result = self.analyze_day(room, date)
            daily_results.append(day_result)
        
        # Agreguj wyniki
        keyword_trends = self.calculate_trends(daily_results)
        
        # Przygotuj raport
        report = {
            'success': True,
            'room': room,
            'analyzed_days': len(analysis_days),
            'date_range': {
                'from': analysis_days[-1] if analysis_days else None,
                'to': analysis_days[0] if analysis_days else None
            },
            'daily_data': daily_results,
            'keyword_trends': keyword_trends,
            'top_keywords': self.get_top_keywords(keyword_trends),
            'generated_at': datetime.now().isoformat()
        }
        
        # Zapisz do cache
        self.save_analysis_cache(room, report)
        
        print(f"✅ ANALIZA ZAKOŃCZONA")
        print(f"🏷️ Znalezione słowa kluczowe: {len(keyword_trends)}")
        
        return report

    def calculate_trends(self, daily_results: List[Dict]) -> Dict:
        """Oblicza trendy dla słów kluczowych"""
        trends = defaultdict(lambda: {
            'daily_data': [],
            'total_mentions': 0,
            'total_views': 0,
            'total_videos': 0,
            'trend_direction': 'stable',
            'trend_strength': 0
        })
        
        # Zbierz dane dzienne dla każdego słowa kluczowego
        for day_result in reversed(daily_results):  # Od najstarszego do najnowszego
            date = day_result['date']
            
            for keyword, data in day_result.get('keywords', {}).items():
                trends[keyword]['daily_data'].append({
                    'date': date,
                    'mentions': data['count'],
                    'views': data['views'],
                    'videos': data['videos']
                })
                
                trends[keyword]['total_mentions'] += data['count']
                trends[keyword]['total_views'] += data['views']
                trends[keyword]['total_videos'] += data['videos']
        
        # Oblicz kierunek trendu
        for keyword, trend_data in trends.items():
            daily_data = trend_data['daily_data']
            if len(daily_data) >= 2:
                # Porównaj pierwszy i ostatni dzień
                first_views = daily_data[0]['views']
                last_views = daily_data[-1]['views']
                
                if last_views > first_views * 1.2:  # +20%
                    trend_data['trend_direction'] = 'rising'
                    trend_data['trend_strength'] = (last_views - first_views) / first_views if first_views > 0 else 0
                elif last_views < first_views * 0.8:  # -20%
                    trend_data['trend_direction'] = 'falling'
                    trend_data['trend_strength'] = (first_views - last_views) / first_views if first_views > 0 else 0
        
        return dict(trends)

    def get_top_keywords(self, keyword_trends: Dict, limit: int = 10) -> List[Dict]:
        """Zwraca top słowa kluczowe sortowane po wyświetleniach"""
        keywords_list = []
        
        for keyword, data in keyword_trends.items():
            keywords_list.append({
                'keyword': keyword,
                'total_views': data['total_views'],
                'total_mentions': data['total_mentions'],
                'total_videos': data['total_videos'],
                'trend_direction': data['trend_direction'],
                'trend_strength': data['trend_strength']
            })
        
        # Sortuj po wyświetleniach
        keywords_list.sort(key=lambda x: x['total_views'], reverse=True)
        
        return keywords_list[:limit]

    def save_analysis_cache(self, room: str, report: Dict):
        """Zapisuje wyniki analizy do cache"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"analysis_{room}_{timestamp}.json"
        filepath = os.path.join(self.analysis_cache_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache zapisany: {filename}")
        except Exception as e:
            print(f"❌ Błąd zapisu cache: {e}")

    def create_demo_data(self, room: str = 'polityka'):
        """Tworzy demo dane do testowania"""
        print(f"🧪 TWORZENIE DEMO DANYCH dla pokoju '{room}'")
        
        # Symuluj 7 dni danych
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            demo_videos = []
            for j in range(5 + i):  # Różna liczba filmów każdego dnia
                demo_videos.append({
                    'title': f"Demo film {j} - Donald Tusk komentuje sytuację",
                    'description': f"Opis filmu z dnia {date} o polityce",
                    'view_count': 1000 + (i * 500) + (j * 100),
                    'like_count': 50 + (j * 5),
                    'published_date': f"{date}T12:0{j}:00Z",
                    'channel_name': f"Demo Kanał {j % 3 + 1}"
                })
            
            demo_data = {
                'room': room,
                'date': date,
                'videos': demo_videos,
                'channels_processed': 3,
                'total_videos': len(demo_videos),
                'demo': True
            }
            
            filename = f"raw_raport_{date}_{room}.json"
            filepath = os.path.join(self.raw_data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(demo_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Demo dzień {date}: {len(demo_videos)} filmów")
        
        print(f"🎉 DEMO DANE UTWORZONE!")

    def format_discord_message(self, analysis_result: Dict) -> str:
        """Formatuje wyniki analizy dla Discord"""
        if not analysis_result.get('success'):
            return f"❌ **BŁĄD ANALIZY**: {analysis_result.get('error', 'Nieznany błąd')}"
        
        room = analysis_result['room']
        days = analysis_result['analyzed_days']
        top_keywords = analysis_result['top_keywords']
        
        message = f"📊 **ANALIZA NAZWISK - #{room.upper()}**\n"
        message += f"📅 Zakres: {days} dni\n\n"
        
        if not top_keywords:
            message += "ℹ️ Brak wykrytych słów kluczowych w analizowanym okresie."
            return message
        
        message += "🏆 **TOP NAZWISKA/SŁOWA:**\n"
        for i, kw in enumerate(top_keywords[:5], 1):
            trend_emoji = {
                'rising': '📈',
                'falling': '📉',
                'stable': '➡️'
            }.get(kw['trend_direction'], '➡️')
            
            message += f"{i}. **{kw['keyword']}** {trend_emoji}\n"
            message += f"   👁️ {kw['total_views']:,} wyświetleń\n"
            message += f"   📺 {kw['total_videos']} filmów\n"
            message += f"   📝 {kw['total_mentions']} wzmianek\n\n"
        
        return message

# DEMO I TESTY
if __name__ == "__main__":
    print("🔍 SYSTEM ANALIZY NAZWISK - WARSZTAT")
    print("=" * 50)
    
    try:
        # Inicjalizuj system
        analyzer = AnalysisNameWorkshop()
        
        # TEST 1: Utwórz demo dane
        print("\n🧪 TEST 1: TWORZENIE DEMO DANYCH")
        analyzer.create_demo_data('polityka')
        
        # TEST 2: Analiza demo danych
        print("\n🧪 TEST 2: ANALIZA DEMO DANYCH")
        result = analyzer.analyze_names('polityka', days=7)
        
        if result['success']:
            print("\n📊 WYNIKI ANALIZY:")
            print(analyzer.format_discord_message(result))
        else:
            print(f"❌ Błąd analizy: {result['error']}")
        
        print(f"\n✅ WSZYSTKIE TESTY ZAKOŃCZONE!")
        
    except Exception as e:
        print(f"❌ BŁĄD SYSTEMU: {e}")
        import traceback
        traceback.print_exc() 