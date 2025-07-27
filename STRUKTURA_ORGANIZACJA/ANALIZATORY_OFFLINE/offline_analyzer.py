#!/usr/bin/env python3
"""
Offline YouTube Data Analyzer - Analiza danych z CSV bez użycia API
Analizuje dane zebrane przez data_collector.py
"""

import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

class OfflineYouTubeAnalyzer:
    def __init__(self, csv_file: str):
        """Inicjalizuje analizator z pliku CSV"""
        self.df = pd.read_csv(csv_file, encoding='utf-8')
        self.csv_file = csv_file
        print(f"📊 Załadowano {len(self.df)} filmów z {csv_file}")
    
    def analyze_names(self, days_back: int = 7) -> Dict:
        """Analizuje nazwiska z ostatnich X dni"""
        # Filtruj dane z ostatnich X dni
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_data = self.df[pd.to_datetime(self.df['Date_of_Publishing']) >= cutoff_date]
        
        if recent_data.empty:
            return {
                'error': f'Brak danych z ostatnich {days_back} dni',
                'total_videos': 0,
                'names_found': 0
            }
        
        # Zbierz wszystkie nazwiska
        all_names = []
        for names_str in recent_data['Names_Extracted'].dropna():
            if names_str:
                names = [name.strip() for name in names_str.split(',') if name.strip()]
                all_names.extend(names)
        
        # Licz wystąpienia
        name_counts = Counter(all_names)
        
        return {
            'total_videos': len(recent_data),
            'names_found': len(all_names),
            'unique_names': len(name_counts),
            'top_names': name_counts.most_common(20),
            'date_range': f"Ostatnie {days_back} dni",
            'data_source': self.csv_file
        }
    
    def analyze_top_videos(self, days_back: int = 7, limit: int = 10) -> Dict:
        """Analizuje najpopularniejsze filmy"""
        # Filtruj dane z ostatnich X dni
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_data = self.df[pd.to_datetime(self.df['Date_of_Publishing']) >= cutoff_date]
        
        if recent_data.empty:
            return {
                'error': f'Brak danych z ostatnich {days_back} dni',
                'total_videos': 0
            }
        
        # Sortuj po wyświetleniach
        top_videos = recent_data.nlargest(limit, 'View_Count')
        
        videos_list = []
        for _, video in top_videos.iterrows():
            videos_list.append({
                'title': video['Title'],
                'channel': video['Channel_Name'],
                'views': int(video['View_Count']),
                'likes': int(video['Like_Count']),
                'comments': int(video['Comment_Count']),
                'date': video['Date_of_Publishing'],
                'link': video['Link'],
                'names': video['Names_Extracted'] if pd.notna(video['Names_Extracted']) else ''
            })
        
        return {
            'total_videos': len(recent_data),
            'top_videos': videos_list,
            'date_range': f"Ostatnie {days_back} dni",
            'data_source': self.csv_file
        }
    
    def analyze_channel_performance(self, days_back: int = 7) -> Dict:
        """Analizuje wydajność kanałów"""
        # Filtruj dane z ostatnich X dni
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_data = self.df[pd.to_datetime(self.df['Date_of_Publishing']) >= cutoff_date]
        
        if recent_data.empty:
            return {
                'error': f'Brak danych z ostatnich {days_back} dni',
                'total_videos': 0
            }
        
        # Grupuj po kanałach
        channel_stats = recent_data.groupby('Channel_Name').agg({
            'View_Count': ['sum', 'mean', 'count'],
            'Like_Count': ['sum', 'mean'],
            'Comment_Count': ['sum', 'mean']
        }).round(2)
        
        # Spłaszcz kolumny
        channel_stats.columns = ['_'.join(col).strip() for col in channel_stats.columns]
        channel_stats = channel_stats.reset_index()
        
        # Sortuj po łącznej liczbie wyświetleń
        channel_stats = channel_stats.sort_values('View_Count_sum', ascending=False)
        
        return {
            'total_videos': len(recent_data),
            'channels_analyzed': len(channel_stats),
            'channel_stats': channel_stats.to_dict('records'),
            'date_range': f"Ostatnie {days_back} dni",
            'data_source': self.csv_file
        }
    
    def analyze_trends(self, days_back: int = 7) -> Dict:
        """Analizuje trendy w danych"""
        # Filtruj dane z ostatnich X dni
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_data = self.df[pd.to_datetime(self.df['Date_of_Publishing']) >= cutoff_date]
        
        if recent_data.empty:
            return {
                'error': f'Brak danych z ostatnich {days_back} dni',
                'total_videos': 0
            }
        
        # Analiza dzienna
        recent_data['Date'] = pd.to_datetime(recent_data['Date_of_Publishing'])
        daily_stats = recent_data.groupby(recent_data['Date'].dt.date).agg({
            'View_Count': 'sum',
            'Like_Count': 'sum',
            'Comment_Count': 'sum',
            'Video_ID': 'count'
        }).rename(columns={'Video_ID': 'video_count'})
        
        # Analiza słów kluczowych w tytułach
        all_titles = ' '.join(recent_data['Title'].dropna().astype(str))
        words = re.findall(r'\b\w+\b', all_titles.lower())
        word_counts = Counter(words)
        
        # Usuń słowa stop
        stop_words = {'i', 'na', 'z', 'do', 'od', 'za', 'o', 'u', 'w', 'a', 'ale', 'czy', 'że', 'to', 'jest', 'był', 'była', 'było', 'są', 'będzie', 'może', 'tylko', 'już', 'nie', 'tak', 'jak', 'co', 'kto', 'gdzie', 'kiedy', 'dlaczego', 'jak', 'ile', 'który', 'jaki', 'jaka', 'jakie'}
        filtered_words = {word: count for word, count in word_counts.items() 
                         if len(word) > 3 and word not in stop_words}
        
        return {
            'total_videos': len(recent_data),
            'daily_stats': daily_stats.to_dict('index'),
            'top_keywords': Counter(filtered_words).most_common(10),
            'date_range': f"Ostatnie {days_back} dni",
            'data_source': self.csv_file
        }
    
    def get_data_summary(self) -> Dict:
        """Zwraca podsumowanie danych"""
        return {
            'total_videos': len(self.df),
            'date_range': f"{self.df['Date_of_Publishing'].min()} - {self.df['Date_of_Publishing'].max()}",
            'channels_count': self.df['Channel_Name'].nunique(),
            'total_views': self.df['View_Count'].sum(),
            'total_likes': self.df['Like_Count'].sum(),
            'total_comments': self.df['Comment_Count'].sum(),
            'videos_with_names': self.df['Names_Extracted'].notna().sum(),
            'data_source': self.csv_file
        }
    
    def export_analysis_to_csv(self, analysis_type: str, days_back: int = 7, filename: str = None):
        """Eksportuje analizę do CSV"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            filename = f"analysis_{analysis_type}_{days_back}dni_{timestamp}.csv"
        
        if analysis_type == 'names':
            result = self.analyze_names(days_back)
            if 'error' in result:
                print(f"❌ {result['error']}")
                return
            
            df = pd.DataFrame(result['top_names'], columns=['Name', 'Count'])
            df.to_csv(filename, index=False, encoding='utf-8')
            
        elif analysis_type == 'videos':
            result = self.analyze_top_videos(days_back)
            if 'error' in result:
                print(f"❌ {result['error']}")
                return
            
            df = pd.DataFrame(result['top_videos'])
            df.to_csv(filename, index=False, encoding='utf-8')
            
        elif analysis_type == 'channels':
            result = self.analyze_channel_performance(days_back)
            if 'error' in result:
                print(f"❌ {result['error']}")
                return
            
            df = pd.DataFrame(result['channel_stats'])
            df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"✅ Analiza eksportowana do: {filename}")

def main():
    """Przykład użycia"""
    # Znajdź najnowszy plik CSV
    import glob
    csv_files = glob.glob("youtube_data_*.csv")
    
    if not csv_files:
        print("❌ Nie znaleziono plików CSV z danymi")
        return
    
    # Użyj najnowszego pliku
    latest_csv = max(csv_files, key=os.path.getctime)
    print(f"📊 Używam pliku: {latest_csv}")
    
    # Utwórz analizator
    analyzer = OfflineYouTubeAnalyzer(latest_csv)
    
    # Pokaż podsumowanie
    summary = analyzer.get_data_summary()
    print(f"\n📈 PODSUMOWANIE DANYCH:")
    print(f"• Łącznie filmów: {summary['total_videos']}")
    print(f"• Zakres dat: {summary['date_range']}")
    print(f"• Liczba kanałów: {summary['channels_count']}")
    print(f"• Łączne wyświetlenia: {summary['total_views']:,}")
    print(f"• Filmy z nazwiskami: {summary['videos_with_names']}")
    
    # Przykładowe analizy
    print(f"\n🔍 ANALIZA NAZWISK (7 dni):")
    names_analysis = analyzer.analyze_names(7)
    if 'error' not in names_analysis:
        print(f"• Przeanalizowanych filmów: {names_analysis['total_videos']}")
        print(f"• Znalezionych nazwisk: {names_analysis['names_found']}")
        print(f"• Unikalnych nazwisk: {names_analysis['unique_names']}")
        print(f"• Top 5 nazwisk:")
        for name, count in names_analysis['top_names'][:5]:
            print(f"  - {name}: {count} wystąpień")
    
    print(f"\n💰 KOSZT: 0 quota (analiza offline)")

if __name__ == "__main__":
    import os
    main() 