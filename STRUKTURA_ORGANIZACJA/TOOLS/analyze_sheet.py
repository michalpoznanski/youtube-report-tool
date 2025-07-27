#!/usr/bin/env python3
"""
ANALIZA OFFLINE - SPAcy + RAPORTY
==================================

Ten skrypt:
1. Analizuje dane CSV z YouTube używając spaCy
2. Generuje raporty z nazwiskami, statystykami
3. Zapisuje wyniki do plików JSON/CSV
4. Bot Discord będzie tylko wyświetlał te wyniki

Uruchomienie:
python3 analyze_sheet.py
"""

import os
import json
import pandas as pd
import spacy
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional

# Załaduj model spaCy
try:
    nlp = spacy.load("pl_core_news_md")
    print("✅ Model spaCy załadowany - analiza offline")
except OSError:
    print("❌ Model spaCy nie znaleziony. Instaluj: python -m spacy download pl_core_news_md")
    exit(1)

class OfflineAnalyzer:
    def __init__(self):
        self.nlp = nlp
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Wczytaj konfigurację kanałów
        try:
            with open('channels_config.json', 'r', encoding='utf-8') as f:
                self.channels_config = json.load(f)
        except:
            self.channels_config = {}
        
    def find_csv_files(self) -> List[str]:
        """Znajduje wszystkie pliki CSV z danymi YouTube"""
        csv_files = []
        
        # Szukaj w głównym katalogu
        for file in os.listdir("."):
            if file.startswith("youtube_data_") and file.endswith(".csv"):
                csv_files.append(file)
        
        # Szukaj w podkatalogach
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.startswith("youtube_data_") and file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))
        
        return sorted(csv_files, key=os.path.getctime, reverse=True)
    
    def load_data(self, csv_file: str) -> pd.DataFrame:
        """Wczytuje dane z CSV"""
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 Załadowano {len(df)} filmów z {csv_file}")
            return df
        except Exception as e:
            print(f"❌ Błąd wczytywania {csv_file}: {e}")
            return pd.DataFrame()
    
    def extract_names_from_text(self, text: str) -> List[str]:
        """Wyciąga nazwiska z tekstu używając spaCy"""
        if not text or pd.isna(text):
            return []
        
        try:
            doc = self.nlp(str(text))
            names = []
            
            for ent in doc.ents:
                if ent.label_ in ['PERSON']:
                    name = ent.text.strip()
                    if len(name) > 2:  # Filtruj krótkie nazwy
                        names.append(name)
            
            return names
        except Exception as e:
            print(f"⚠️ Błąd analizy tekstu: {e}")
            return []
    
    def analyze_names(self, df: pd.DataFrame) -> Dict:
        """Analizuje nazwiska w danych"""
        print("🔍 Analizuję nazwiska...")
        
        all_names = []
        name_videos = defaultdict(list)
        name_channels = defaultdict(set)
        
        for idx, row in df.iterrows():
            # Analizuj tytuł
            title_names = self.extract_names_from_text(row.get('Title', ''))
            
            # Analizuj opis
            desc_names = self.extract_names_from_text(row.get('Description', ''))
            
            # Połącz wszystkie nazwiska
            video_names = list(set(title_names + desc_names))
            
            for name in video_names:
                all_names.append(name)
                name_videos[name].append({
                                    'video_id': row.get('Video_ID', ''),
                'title': row.get('Title', ''),
                'channel': row.get('Channel_Name', ''),
                'views': row.get('View_Count', 0),
                'published_date': row.get('Date_of_Publishing', ''),
                    'source': 'title' if name in title_names else 'description'
                })
                name_channels[name].add(row.get('Channel_Name', ''))
        
        # Statystyki nazwisk
        name_counts = Counter(all_names)
        
        # Oblicz siłę nazwiska
        name_strength = {}
        for name, count in name_counts.items():
            videos = name_videos[name]
            total_views = sum(v.get('views', 0) for v in videos)
            channels_count = len(name_channels[name])
            
            # Algorytm siły nazwiska
            views_score = min(total_views / 1000000, 1.0)  # Normalizuj do 1M wyświetleń
            frequency_score = min(count / 10, 1.0)  # Normalizuj do 10 wystąpień
            network_score = min(channels_count / 5, 1.0)  # Normalizuj do 5 kanałów
            
            strength = (views_score * 0.5) + (frequency_score * 0.3) + (network_score * 0.2)
            name_strength[name] = {
                'count': count,
                'total_views': total_views,
                'channels': list(name_channels[name]),
                'strength': round(strength, 3),
                'videos': videos
            }
        
        return {
            'total_names': len(name_counts),
            'unique_names': len(set(all_names)),
            'name_counts': dict(name_counts),
            'name_strength': name_strength,
            'top_names': sorted(name_strength.items(), key=lambda x: x[1]['strength'], reverse=True)[:20]
        }
    
    def analyze_channels(self, df: pd.DataFrame) -> Dict:
        """Analizuje kanały"""
        print("📺 Analizuję kanały...")
        
        channel_stats = df.groupby('Channel_Name').agg({
            'View_Count': ['count', 'sum', 'mean']
        }).round(2)
        
        # Zmień nazwy kolumn
        channel_stats.columns = ['video_count', 'total_views', 'avg_views']
        channel_stats = channel_stats.sort_values('total_views', ascending=False)
        
        return {
            'total_channels': int(len(channel_stats)),
            'total_videos': int(len(df)),
            'total_views': int(df['View_Count'].sum()),
            'avg_views_per_video': float(df['View_Count'].mean()),
            'channel_ranking': channel_stats.to_dict('index')
        }
    
    def analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analizuje trendy czasowe"""
        print("📈 Analizuję trendy...")
        
        # Konwertuj daty
        df['Date'] = pd.to_datetime(df['Date_of_Publishing'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        # Grupuj po dniach
        daily_stats = df.groupby(df['Date'].dt.date).agg({
            'View_Count': ['count', 'sum']
        }).round(2)
        
        daily_stats.columns = ['video_count', 'total_views']
        
        return {
            'date_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d')
            },
            'daily_stats': {str(k): v for k, v in daily_stats.to_dict('index').items()},
            'total_days': int(len(daily_stats))
        }
    
    def generate_report(self, csv_file: str, category: str = None) -> Dict:
        """Generuje pełny raport"""
        print(f"\n📋 GENERUJĘ RAPORT DLA: {csv_file}")
        if category:
            print(f"🎯 KATEGORIA: {category.upper()}")
        print("=" * 50)
        
        # Wczytaj dane
        df = self.load_data(csv_file)
        if df.empty:
            return {}
        
        # Określ kategorię na podstawie nazwy pliku jeśli nie podano
        if not category:
            if 'showbiz' in csv_file.lower():
                category = 'showbiz'
            elif 'politics' in csv_file.lower():
                category = 'politics'
            elif 'motoryzacja' in csv_file.lower():
                category = 'motoryzacja'
            elif 'podcast' in csv_file.lower():
                category = 'podcast'
            else:
                category = 'unknown'
        
        # Analizy
        names_analysis = self.analyze_names(df)
        channels_analysis = self.analyze_channels(df)
        trends_analysis = self.analyze_trends(df)
        
        # Pełny raport
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_file': csv_file,
                'category': category,
                'data_points': len(df)
            },
            'names_analysis': names_analysis,
            'channels_analysis': channels_analysis,
            'trends_analysis': trends_analysis
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = None) -> str:
        """Zapisuje raport do pliku"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.json"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Raport zapisany: {filepath}")
        return filepath
    
    def print_summary(self, report: Dict):
        """Wyświetla podsumowanie raportu"""
        if not report:
            print("❌ Brak danych do analizy")
            return
        
        print("\n" + "="*60)
        print("📊 PODSUMOWANIE RAPORTU")
        print("="*60)
        
        # Metadane
        meta = report['metadata']
        print(f"📅 Wygenerowano: {meta['generated_at']}")
        print(f"📁 Plik źródłowy: {meta['source_file']}")
        print(f"🎯 Kategoria: {meta.get('category', 'unknown').upper()}")
        print(f"📊 Punkty danych: {meta['data_points']}")
        
        # Nazwiska
        names = report['names_analysis']
        print(f"\n👥 NAZWISKA:")
        print(f"   • Unikalne nazwiska: {names['unique_names']}")
        print(f"   • Łączne wystąpienia: {names['total_names']}")
        
        if names['top_names']:
            print(f"   • TOP 5 NAZWISK:")
            for i, (name, stats) in enumerate(names['top_names'][:5], 1):
                print(f"     {i}. {name} (siła: {stats['strength']}, wyświetlenia: {stats['total_views']:,})")
        
        # Kanały
        channels = report['channels_analysis']
        print(f"\n📺 KANAŁY:")
        print(f"   • Liczba kanałów: {channels['total_channels']}")
        print(f"   • Łączne filmy: {channels['total_videos']}")
        print(f"   • Łączne wyświetlenia: {channels['total_views']:,}")
        print(f"   • Średnie wyświetlenia/film: {channels['avg_views_per_video']:,.0f}")
        
        # Trendy
        trends = report['trends_analysis']
        print(f"\n📈 TRENDY:")
        print(f"   • Okres: {trends['date_range']['start']} - {trends['date_range']['end']}")
        print(f"   • Liczba dni: {trends['total_days']}")
    
    def run_analysis(self):
        """Główna funkcja analizy"""
        print("🚀 URUCHAMIAM ANALIZĘ OFFLINE")
        print("=" * 50)
        
        # Znajdź pliki CSV
        csv_files = self.find_csv_files()
        
        if not csv_files:
            print("❌ Nie znaleziono plików CSV z danymi YouTube")
            print("💡 Uruchom najpierw: !raport")
            return
        
        print(f"📁 Znaleziono {len(csv_files)} plików CSV:")
        for i, file in enumerate(csv_files[:5], 1):  # Pokaż pierwsze 5
            print(f"   {i}. {file}")
        
        # Analizuj najnowszy plik
        latest_file = csv_files[0]
        print(f"\n🎯 Analizuję najnowszy plik: {latest_file}")
        
        # Określ kategorię na podstawie nazwy pliku
        category = None
        if 'showbiz' in latest_file.lower():
            category = 'showbiz'
        elif 'politics' in latest_file.lower():
            category = 'politics'
        elif 'motoryzacja' in latest_file.lower():
            category = 'motoryzacja'
        elif 'podcast' in latest_file.lower():
            category = 'podcast'
        
        # Generuj raport
        report = self.generate_report(latest_file, category)
        
        if report:
            # Zapisz raport
            report_file = self.save_report(report)
            
            # Wyświetl podsumowanie
            self.print_summary(report)
            
            print(f"\n✅ ANALIZA ZAKOŃCZONA!")
            print(f"📄 Raport: {report_file}")
            print(f"🤖 Bot Discord może teraz wyświetlić te wyniki")
        else:
            print("❌ Nie udało się wygenerować raportu")

def main():
    """Główna funkcja"""
    analyzer = OfflineAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()