#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 SYSTEM !ŚLEDŹ - WARSZTAT V2
================================

Uproszczony system dodawania kanałów do pokojów Discord.
NOWA FILOZOFIA:
- Każdy pokój ma swoje kanały (bez kategorii)
- Proste dodawanie bez skomplikowanego mapowania
- Kanały mogą być w wielu pokojach jednocześnie

UŻYCIE:
!śledź [linki YouTube]

BEZPIECZEŃSTWO:
- Praca w warsztacie, nie modyfikuje głównego bota
- Testowanie bez prawdziwego API
- Suche uruchomienia
"""

import json
import re
import sys
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

# Dodaj główny folder do path
sys.path.append('..')
from quota_manager import QuotaManager

class SledzSystemV2:
    def __init__(self, channels_config_path='channels_config.json', api_key=None):
        """
        Inicjalizacja systemu śledzenia kanałów
        
        Args:
            channels_config_path: Ścieżka do pliku konfiguracji
            api_key: Klucz API YouTube (None = tryb testowy)
        """
        self.config_path = channels_config_path
        self.api_key = api_key
        self.test_mode = api_key is None
        
        # Załaduj konfigurację
        self.channels_config = self._load_config()
        
        # Inicjalizuj QuotaManager jeśli mamy API
        self.quota_manager = None
        if not self.test_mode:
            self.quota_manager = QuotaManager(api_key)
    
    def _load_config(self) -> Dict:
        """Wczytaj konfigurację kanałów"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Migruj starą strukturę do nowej jeśli potrzeba
            if 'channels' not in config:
                # Stara struktura: {category: [channels]}
                # Nowa struktura: {channels: {room_name: [channels]}}
                new_config = {'channels': {}}
                
                # Konwertuj kategorie na pokoje
                for category, channels in config.items():
                    if isinstance(channels, list):
                        # Mapuj kategorie na domyślne nazwy pokojów
                        room_mapping = {
                            'Politics': 'polityka',
                            'Showbiz': 'showbiz',
                            'Motoryzacja': 'motoryzacja', 
                            'Podcast': 'podcast',
                            'AI': 'ai'
                        }
                        room_name = room_mapping.get(category, category.lower())
                        new_config['channels'][room_name] = channels
                
                return new_config
            
            return config
            
        except FileNotFoundError:
            return {'channels': {}}
        except Exception as e:
            print(f"❌ Błąd wczytywania konfiguracji: {e}")
            return {'channels': {}}
    
    def _save_config(self) -> bool:
        """Zapisz konfigurację do pliku"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.channels_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu konfiguracji: {e}")
            return False
    
    def extract_youtube_links(self, message: str) -> Tuple[List[str], List[str]]:
        """
        Wyciągnij linki YouTube z wiadomości
        
        Returns:
            Tuple[List[str], List[str]]: (channel_links, video_links)
        """
        # Wzorce dla kanałów
        channel_patterns = [
            r'https://www\.youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'https://www\.youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'https://www\.youtube\.com/@([a-zA-Z0-9_.-]+)',
            r'https://youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'https://youtube\.com/@([a-zA-Z0-9_.-]+)'
        ]
        
        # Wzorce dla filmów/shortsów
        video_patterns = [
            r'https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https://youtu\.be/([a-zA-Z0-9_-]+)',
            r'https://www\.youtube\.com/shorts/([a-zA-Z0-9_-]+)',
            r'https://youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https://youtube\.com/shorts/([a-zA-Z0-9_-]+)'
        ]
        
        channel_links = []
        video_links = []
        
        # Znajdź kanały
        for pattern in channel_patterns:
            matches = re.findall(pattern, message)
            channel_links.extend(matches)
        
        # Znajdź filmy
        for pattern in video_patterns:
            matches = re.findall(pattern, message)
            video_links.extend(matches)
        
        # Usuń duplikaty zachowując kolejność
        channel_links = list(dict.fromkeys(channel_links))
        video_links = list(dict.fromkeys(video_links))
        
        return channel_links, video_links
    
    def resolve_channel_ids(self, channel_links: List[str], video_links: List[str]) -> Tuple[List[str], int]:
        """
        Konwertuj linki na Channel ID
        
        Returns:
            Tuple[List[str], int]: (channel_ids, quota_cost)
        """
        channel_ids = []
        quota_cost = 0
        
        # Przetwórz linki kanałów
        for link in channel_links:
            if link.startswith('UC') and len(link) == 24:
                # To już jest Channel ID
                channel_ids.append(link)
            else:
                # To handle lub inne - w trybie testowym symuluj
                if self.test_mode:
                    # Symuluj Channel ID
                    simulated_id = f"UC{''.join(link.split('@')[-1].split('/')[-1])}_TEST"[:24].ljust(24, '0')
                    channel_ids.append(simulated_id)
                    quota_cost += 100 if '@' in link else 1
                else:
                    # TODO: Prawdziwa konwersja przez API
                    # Placeholder - trzeba będzie zaimplementować
                    channel_ids.append(f"UC_CONVERTED_{link}")
                    quota_cost += 100 if '@' in link else 1
        
        # Przetwórz linki filmów (wyciągnij Channel ID)
        for video_id in video_links:
            if self.test_mode:
                # Symuluj Channel ID dla filmu
                simulated_id = f"UC_VIDEO_{video_id[:10]}_TEST".ljust(24, '0')
                channel_ids.append(simulated_id)
                quota_cost += 1  # Videos API: 1 quota
            else:
                # TODO: Prawdziwa konwersja przez API
                channel_ids.append(f"UC_FROM_VIDEO_{video_id}")
                quota_cost += 1
        
        # Usuń duplikaty
        channel_ids = list(dict.fromkeys(channel_ids))
        
        return channel_ids, quota_cost
    
    def add_channels_to_room(self, room_name: str, channel_ids: List[str]) -> Dict:
        """
        Dodaj kanały do konkretnego pokoju
        
        Returns:
            Dict: Raport z operacji
        """
        # Upewnij się że pokój istnieje
        if 'channels' not in self.channels_config:
            self.channels_config['channels'] = {}
        
        if room_name not in self.channels_config['channels']:
            self.channels_config['channels'][room_name] = []
        
        # Sprawdź co już istnieje
        existing_channels = self.channels_config['channels'][room_name]
        new_channels = []
        already_tracked = []
        
        for channel_id in channel_ids:
            if channel_id not in existing_channels:
                self.channels_config['channels'][room_name].append(channel_id)
                new_channels.append(channel_id)
            else:
                already_tracked.append(channel_id)
        
        # Sprawdź kanały w innych pokojach
        cross_room_channels = []
        for other_room, other_channels in self.channels_config['channels'].items():
            if other_room != room_name:
                for channel_id in new_channels:
                    if channel_id in other_channels:
                        cross_room_channels.append((channel_id, other_room))
        
        return {
            'room_name': room_name,
            'new_channels': new_channels,
            'already_tracked': already_tracked,
            'cross_room_channels': cross_room_channels,
            'total_in_room': len(self.channels_config['channels'][room_name])
        }
    
    def process_sledz_command(self, room_name: str, message: str) -> Dict:
        """
        Główna logika komendy !śledź
        
        Args:
            room_name: Nazwa pokoju Discord
            message: Wiadomość z linkami
            
        Returns:
            Dict: Kompletny raport z operacji
        """
        # Krok 1: Wyciągnij linki
        channel_links, video_links = self.extract_youtube_links(message)
        
        if not channel_links and not video_links:
            return {
                'success': False,
                'error': 'Nie znaleziono linków YouTube w wiadomości',
                'supported_formats': [
                    'Kanały: /channel/, /@username, /c/name',
                    'Filmy: /watch?v=, /shorts/, youtu.be/'
                ]
            }
        
        # Krok 2: Konwertuj na Channel ID
        channel_ids, quota_cost = self.resolve_channel_ids(channel_links, video_links)
        
        # Krok 3: Sprawdź quota (jeśli nie test)
        if not self.test_mode and self.quota_manager and quota_cost > 0:
            can_perform, quota_details = self.quota_manager.can_perform_operation(
                'sledz_channels', 
                {'estimated_cost': quota_cost}
            )
            
            if not can_perform:
                return {
                    'success': False,
                    'error': 'Niewystarczające quota',
                    'quota_cost': quota_cost,
                    'quota_details': quota_details
                }
        
        # Krok 4: Dodaj kanały do pokoju
        add_result = self.add_channels_to_room(room_name, channel_ids)
        
        # Krok 5: Zapisz konfigurację
        save_success = self._save_config()
        
        # Krok 6: Przygotuj raport
        return {
            'success': True,
            'room_name': room_name,
            'found_links': {
                'channels': len(channel_links),
                'videos': len(video_links),
                'total': len(channel_links) + len(video_links)
            },
            'processed_channels': len(channel_ids),
            'quota_cost': quota_cost,
            'add_result': add_result,
            'config_saved': save_success,
            'test_mode': self.test_mode
        }
    
    def get_room_channels(self, room_name: str) -> List[str]:
        """Pobierz kanały dla konkretnego pokoju"""
        if 'channels' not in self.channels_config:
            return []
        return self.channels_config['channels'].get(room_name, [])
    
    def get_all_rooms(self) -> Dict[str, int]:
        """Pobierz wszystkie pokoje i liczbę kanałów"""
        if 'channels' not in self.channels_config:
            return {}
        
        return {
            room: len(channels) 
            for room, channels in self.channels_config['channels'].items()
        }

# ===== FUNKCJE TESTOWE =====

def test_link_extraction():
    """Test wyciągania linków z wiadomości"""
    system = SledzSystemV2()
    
    test_message = """
    Dodaj te kanały:
    https://www.youtube.com/@PolitykaNazywo 
    https://www.youtube.com/channel/UCGAqh18kKGpb8fBwz8Xv-bA
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    https://youtu.be/dQw4w9WgXcQ
    """
    
    channel_links, video_links = system.extract_youtube_links(test_message)
    
    print("🔍 TEST WYCIĄGANIA LINKÓW:")
    print(f"📺 Kanały: {channel_links}")
    print(f"🎬 Filmy: {video_links}")
    
    return len(channel_links) > 0 and len(video_links) > 0

def test_sledz_command():
    """Test pełnej komendy !śledź"""
    system = SledzSystemV2()
    
    test_message = """
    https://www.youtube.com/@RadioZET
    https://www.youtube.com/channel/UCGAqh18kKGpb8fBwz8Xv-bA
    https://www.youtube.com/watch?v=test123
    """
    
    result = system.process_sledz_command('polityka', test_message)
    
    print("\n🎯 TEST KOMENDY !ŚLEDŹ:")
    print(f"✅ Sukces: {result['success']}")
    if result['success']:
        print(f"📍 Pokój: {result['room_name']}")
        print(f"🔗 Znalezione linki: {result['found_links']}")
        print(f"📺 Przetworzono kanałów: {result['processed_channels']}")
        print(f"💰 Koszt quota: {result['quota_cost']}")
        print(f"🆕 Nowe kanały: {len(result['add_result']['new_channels'])}")
        print(f"🔄 Już śledzone: {len(result['add_result']['already_tracked'])}")
        print(f"📊 Łącznie w pokoju: {result['add_result']['total_in_room']}")
    else:
        print(f"❌ Błąd: {result['error']}")
    
    return result['success']

if __name__ == "__main__":
    print("🎯 SYSTEM !ŚLEDŹ V2 - TESTY W WARSZTACIE")
    print("=" * 50)
    
    # Uruchom testy
    test1 = test_link_extraction()
    test2 = test_sledz_command()
    
    print(f"\n📊 WYNIKI TESTÓW:")
    print(f"🔗 Wyciąganie linków: {'✅' if test1 else '❌'}")
    print(f"🎯 Komenda !śledź: {'✅' if test2 else '❌'}")
    
    if test1 and test2:
        print("\n🚀 SYSTEM GOTOWY DO DALSZYCH TESTÓW!")
    else:
        print("\n⚠️ SYSTEM WYMAGA POPRAWEK") 