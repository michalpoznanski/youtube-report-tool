#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 SYSTEM !ŚLEDŹ - WERSJA PRODUKCYJNA
====================================

Gotowy system dodawania kanałów do pokojów Discord.
FILOZOFIA:
- Każdy pokój ma swoje kanały (bez kategorii)
- Proste dodawanie bez skomplikowanego mapowania
- Kanały mogą być w wielu pokojach jednocześnie

UŻYCIE W DISCORD BOT:
@bot.command(name='śledź')
async def track_channels(ctx, *, message: str = None):
    system = SledzSystem(api_key=YOUTUBE_API_KEY)
    result = system.process_sledz_command(ctx.channel.name, message)
    # ... obsługa wyniku
"""

import json
import re
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

class SledzSystem:
    def __init__(self, channels_config_path='channels_config.json', api_key=None):
        """
        Inicjalizacja systemu śledzenia kanałów
        
        Args:
            channels_config_path: Ścieżka do pliku konfiguracji
            api_key: Klucz API YouTube (wymagany w produkcji)
        """
        self.config_path = channels_config_path
        self.api_key = api_key
        
        # Załaduj konfigurację
        self.channels_config = self._load_config()
        
        # Inicjalizuj QuotaManager jeśli mamy API
        self.quota_manager = None
        if api_key:
            try:
                from quota_manager import QuotaManager
                self.quota_manager = QuotaManager(api_key)
            except ImportError:
                print("⚠️ QuotaManager niedostępny - quota nie będzie monitorowane")
    
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
        Konwertuj linki na Channel ID używając prawdziwego API YouTube
        
        Returns:
            Tuple[List[str], int]: (channel_ids, quota_cost)
        """
        channel_ids = []
        quota_cost = 0
        
        if not self.api_key:
            return [], 0
        
        # Przetwórz linki kanałów
        for link in channel_links:
            if link.startswith('UC') and len(link) == 24:
                # To już jest Channel ID
                channel_ids.append(link)
            else:
                # To handle lub inne - konwertuj przez API
                try:
                    if link.startswith('@') or '@' in link:
                        # Handle - użyj Search API
                        search_url = "https://www.googleapis.com/youtube/v3/search"
                        params = {
                            'part': 'snippet',
                            'type': 'channel',
                            'q': link.replace('@', ''),
                            'key': self.api_key,
                            'maxResults': 1
                        }
                        response = requests.get(search_url, params=params)
                        data = response.json()
                        
                        if data.get('items'):
                            channel_id = data['items'][0]['snippet']['channelId']
                            channel_ids.append(channel_id)
                            quota_cost += 100  # Search API koszt
                            
                            # Zaloguj quota
                            if self.quota_manager:
                                self.quota_manager.log_operation('search', 100, {
                                    'handle': link,
                                    'operation': 'sledz_channels'
                                })
                    else:
                        # Username lub /c/ - użyj Channels API
                        channels_url = "https://www.googleapis.com/youtube/v3/channels"
                        params = {
                            'part': 'id',
                            'forUsername': link,
                            'key': self.api_key
                        }
                        response = requests.get(channels_url, params=params)
                        data = response.json()
                        
                        if data.get('items'):
                            channel_id = data['items'][0]['id']
                            channel_ids.append(channel_id)
                            quota_cost += 1  # Channels API koszt
                            
                            # Zaloguj quota
                            if self.quota_manager:
                                self.quota_manager.log_operation('channels_list', 1, {
                                    'username': link,
                                    'operation': 'sledz_channels'
                                })
                        else:
                            # Fallback - może to już jest Channel ID
                            channel_ids.append(link)
                            
                except Exception as e:
                    print(f"⚠️ Błąd konwersji kanału {link}: {e}")
                    # W przypadku błędu, spróbuj użyć jako Channel ID
                    channel_ids.append(link)
        
        # Przetwórz linki filmów (wyciągnij Channel ID)
        for video_id in video_links:
            try:
                videos_url = "https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'part': 'snippet',
                    'id': video_id,
                    'key': self.api_key
                }
                response = requests.get(videos_url, params=params)
                data = response.json()
                
                if data.get('items'):
                    channel_id = data['items'][0]['snippet']['channelId']
                    channel_ids.append(channel_id)
                    quota_cost += 1  # Videos API koszt
                    
                    # Zaloguj quota
                    if self.quota_manager:
                        self.quota_manager.log_operation('videos_list', 1, {
                            'video_id': video_id,
                            'operation': 'sledz_channels'
                        })
                        
            except Exception as e:
                print(f"⚠️ Błąd konwersji filmu {video_id}: {e}")
                continue
        
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
        Główna logika komendy !śledź - WERSJA PRODUKCYJNA
        
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
        
        # Krok 3: Sprawdź quota
        if self.quota_manager and quota_cost > 0:
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
            'config_saved': save_success
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