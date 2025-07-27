#!/usr/bin/env python3
"""
System AI do automatycznego znajdowania polskich kanałów showbiz
"""

import os
import asyncio
import json
import pandas as pd
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone

class AIChannelFinder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def load_existing_data(self) -> pd.DataFrame:
        """Wczytuje istniejące dane z CSV"""
        try:
            # Znajdź najnowszy plik CSV
            csv_files = [f for f in os.listdir('.') if f.startswith('youtube_data_') and f.endswith('.csv')]
            if not csv_files:
                return pd.DataFrame()
            
            latest_file = max(csv_files)
            df = pd.read_csv(latest_file, encoding='utf-8')
            print(f"📊 Załadowano {len(df)} filmów z {latest_file}")
            return df
        except Exception as e:
            print(f"❌ Błąd wczytywania danych: {e}")
            return pd.DataFrame()
    
    def extract_polish_names(self, df: pd.DataFrame) -> Counter:
        """Wyciąga polskie nazwiska z istniejących danych"""
        all_names = []
        
        for names_str in df['Names_Extracted'].dropna():
            if names_str:
                names = [name.strip() for name in names_str.split(',') if name.strip()]
                all_names.extend(names)
        
        # Licz wystąpienia nazwisk
        name_counter = Counter(all_names)
        
        # Filtruj tylko polskie nazwiska (można dodać bardziej zaawansowaną logikę)
        polish_names = {name: count for name, count in name_counter.items() 
                       if count >= 2 and len(name.split()) >= 2}  # Minimum 2 słowa i 2 wystąpienia
        
        return Counter(polish_names)
    
    async def find_channels_by_names(self, names: list, max_results: int = 10) -> list:
        """Znajduje kanały na podstawie nazwisk"""
        found_channels = []
        
        for name in names[:5]:  # Sprawdź top 5 nazwisk
            try:
                # Szukaj filmów z tym nazwiskiem
                response = self.youtube.search().list(
                    part='snippet',
                    q=name,
                    type='video',
                    maxResults=20,
                    publishedAfter=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                    regionCode='PL'  # Tylko polskie wyniki
                ).execute()
                
                for item in response.get('items', []):
                    channel_id = item['snippet']['channelId']
                    channel_title = item['snippet']['channelTitle']
                    
                    # Sprawdź czy kanał już nie jest w naszej liście
                    if not self.is_channel_tracked(channel_id):
                        found_channels.append({
                            'channel_id': channel_id,
                            'channel_title': channel_title,
                            'search_term': name,
                            'video_title': item['snippet']['title']
                        })
                
                await asyncio.sleep(0.5)  # Przerwa między requestami
                
            except HttpError as e:
                print(f"❌ Błąd API dla nazwiska {name}: {e}")
                continue
        
        # Usuń duplikaty i zwróć unikalne kanały
        unique_channels = []
        seen_ids = set()
        
        for channel in found_channels:
            if channel['channel_id'] not in seen_ids:
                unique_channels.append(channel)
                seen_ids.add(channel['channel_id'])
        
        return unique_channels[:max_results]
    
    def is_channel_tracked(self, channel_id: str) -> bool:
        """Sprawdza czy kanał jest już śledzony"""
        try:
            with open('channels_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for category, channels in config.items():
                if channel_id in channels:
                    return True
            
            return False
        except Exception:
            return False
    
    def save_suggestions(self, suggestions: list):
        """Zapisuje sugestie do pliku"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"channel_suggestions_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Sugestie zapisane do: {filename}")
        return filename

async def main():
    """Główna funkcja"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Brak klucza API YouTube")
        return
    
    finder = AIChannelFinder(api_key)
    
    # Wczytaj istniejące dane
    df = finder.load_existing_data()
    if df.empty:
        print("❌ Brak danych do analizy")
        return
    
    # Wyciągnij polskie nazwiska
    polish_names = finder.extract_polish_names(df)
    print(f"🔍 Znaleziono {len(polish_names)} polskich nazwisk:")
    
    for name, count in polish_names.most_common(10):
        print(f"   • {name} ({count} wystąpień)")
    
    # Znajdź kanały na podstawie nazwisk
    print("\n🔍 Szukam nowych kanałów showbiz...")
    suggestions = await finder.find_channels_by_names(list(polish_names.keys()))
    
    if suggestions:
        print(f"\n✅ Znaleziono {len(suggestions)} potencjalnych kanałów:")
        for i, channel in enumerate(suggestions, 1):
            print(f"   {i}. {channel['channel_title']}")
            print(f"      ID: {channel['channel_id']}")
            print(f"      Szukane nazwisko: {channel['search_term']}")
            print(f"      Przykładowy film: {channel['video_title'][:50]}...")
            print()
        
        # Zapisz sugestie
        finder.save_suggestions(suggestions)
    else:
        print("❌ Nie znaleziono nowych kanałów")

if __name__ == "__main__":
    asyncio.run(main()) 