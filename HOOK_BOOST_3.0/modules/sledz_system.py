#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SLEDZ SYSTEM - HOOK BOOST 3.0
==============================

System dodawania kanałów YouTube do śledzenia.
Obsługuje @handle (1 quota) i Channel ID (0 quota).

AUTOR: Hook Boost 3.0 - Ultra Lean
WERSJA: 3.0 (Simplified)
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional

class SledzSystem:
    """System !śledź z monitorowaniem quota"""
    
    def __init__(self, channels_config_path="data/channels_config.json", api_key=None):
        self.channels_config_path = channels_config_path
        self.api_key = api_key
        self.channels_config = {}
        
        # Koszty quota
        self.HANDLE_COST = 1  # @handle - 1 quota
        self.CHANNEL_ID_COST = 0  # Channel ID - darmowe
        
        # QuotaManager usunięty - ultra lean mode
        print("⚡ SledzSystem: ultra lean mode (bez quota managera)")
        
        self._load_config()
    
    def _load_config(self):
        """Ładuje konfigurację kanałów"""
        try:
            if os.path.exists(self.channels_config_path):
                with open(self.channels_config_path, 'r', encoding='utf-8') as f:
                    self.channels_config = json.load(f)
            
            if 'channels' not in self.channels_config:
                self.channels_config['channels'] = {}
                
        except Exception as e:
            print(f"Błąd ładowania config: {e}")
            self.channels_config = {'channels': {}}
    
    def _save_config(self):
        """Zapisuje konfigurację kanałów"""
        try:
            # Upewnij się, że katalog istnieje
            os.makedirs(os.path.dirname(self.channels_config_path), exist_ok=True)
            
            with open(self.channels_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.channels_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu config: {e}")
    
    def _analyze_single_link(self, link):
        """Analizuje pojedynczy link - @handle i Channel ID dozwolone!"""
        
        link = link.strip()
        channel_id_pattern = re.compile(r'UC[a-zA-Z0-9_-]{22}')
        
        # Channel ID - 0 quota (DARMOWE!)
        if channel_id_pattern.fullmatch(link) or 'youtube.com/channel/UC' in link:
            return {
                'link': link,
                'type': 'channel_id',
                'cost': self.CHANNEL_ID_COST,
                'description': 'Channel ID - darmowe'
            }
        
        # @handle - 1 quota
        if '@' in link and ('youtube.com/@' in link or link.startswith('@')):
            return {
                'link': link,
                'type': 'handle', 
                'cost': self.HANDLE_COST,
                'description': '@handle - 1 quota'
            }
        
        # WSZYSTKIE INNE FORMATY - ODRZUĆ!
        if 'youtube.com/watch' in link or 'youtu.be/' in link:
            error_msg = '❌ Linki do filmów nie są dozwolone - użyj @handle kanału lub Channel ID'
        elif '/c/' in link:
            error_msg = '❌ Linki /c/ nie są dozwolone - użyj @handle lub Channel ID'
        elif '/user/' in link:
            error_msg = '❌ Linki /user/ nie są dozwolone - użyj @handle lub Channel ID'
        else:
            error_msg = '❌ Nieznany format linku - użyj @handle lub Channel ID'
        
        return {
            'link': link,
            'type': 'forbidden',
            'cost': 0,
            'description': error_msg
        }
    
    def analyze_links_cost(self, message):
        """Analizuje koszt quota dla wszystkich linków"""
        if not message:
            return {'total_cost': 0, 'links': [], 'forbidden': []}
        
        lines = message.strip().split('\n')
        total_cost = 0
        valid_links = []
        forbidden_links = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            analysis = self._analyze_single_link(line)
            
            if analysis['type'] == 'forbidden':
                forbidden_links.append(analysis['description'])
            else:
                valid_links.append(analysis)
                total_cost += analysis['cost']
        
        return {
            'total_cost': total_cost,
            'links': valid_links,
            'forbidden': forbidden_links
        }
    
    def _resolve_channel_id(self, link_data):
        """Rozwiązuje @handle do Channel ID"""
        if link_data['type'] == 'channel_id':
            # Wyciągnij Channel ID z linku
            if 'youtube.com/channel/' in link_data['link']:
                channel_id = link_data['link'].split('youtube.com/channel/')[-1].split('?')[0]
            else:
                channel_id = link_data['link']
            
            return {
                'success': True,
                'channel_id': channel_id,
                'cost': link_data['cost']
            }
        
        elif link_data['type'] == 'handle':
            handle = link_data['link']
            if 'youtube.com/@' in handle:
                handle = handle.split('youtube.com/@')[-1].split('?')[0]
            elif handle.startswith('@'):
                handle = handle[1:]
            
            try:
                # Lepsze API do rozwiązywania @handle
                url = f"https://www.googleapis.com/youtube/v3/channels"
                params = {
                    'part': 'id',
                    'forHandle': handle,
                    'key': self.api_key
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if data.get('items'):
                    channel_id = data['items'][0]['id']
                    return {
                        'success': True,
                        'channel_id': channel_id,
                        'cost': link_data['cost']
                    }
                else:
                    # Fallback - Search API
                    url = f"https://www.googleapis.com/youtube/v3/search"
                    params = {
                        'part': 'snippet',
                        'q': f"@{handle}",
                        'type': 'channel',
                        'maxResults': 1,
                        'key': self.api_key
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data.get('items'):
                        channel_id = data['items'][0]['snippet']['channelId']
                        return {
                            'success': True,
                            'channel_id': channel_id,
                            'cost': link_data['cost']
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Kanał @{handle} nie został znaleziony'
                        }
                        
            except requests.exceptions.Timeout:
                return {
                    'success': False,
                    'error': f'Timeout przy rozwiązywaniu @{handle}'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Błąd API: {str(e)}'
                }
        
        return {
            'success': False,
            'error': 'Nieznany typ linku'
        }
    
    def add_channels_to_room(self, room_name, links_analysis):
        """Dodaje kanały do pokoju"""
        if not links_analysis['links']:
            return {
                'success': False,
                'error': 'Brak dozwolonych linków'
            }
        
        # Quota check usunięty - ultra lean mode
        
        # Rozwiąż wszystkie linki
        resolved_channels = []
        total_cost_used = 0
        
        for link_data in links_analysis['links']:
            result = self._resolve_channel_id(link_data)
            
            if result['success']:
                resolved_channels.append(result['channel_id'])
                total_cost_used += result['cost']
            else:
                print(f"❌ Błąd rozwiązywania {link_data['link']}: {result['error']}")
        
        if not resolved_channels:
            return {
                'success': False,
                'error': 'Nie udało się rozwiązać żadnego linku'
            }
        
        # Dodaj do konfiguracji
        if 'channels' not in self.channels_config:
            self.channels_config['channels'] = {}
        
        if room_name not in self.channels_config['channels']:
            self.channels_config['channels'][room_name] = []
        
        # Dodaj nowe kanały (bez duplikatów)
        existing = set(self.channels_config['channels'][room_name])
        new_channels = []
        
        for channel_id in resolved_channels:
            if channel_id not in existing:
                self.channels_config['channels'][room_name].append(channel_id)
                new_channels.append(channel_id)
        
        # Zapisz konfigurację
        self._save_config()
        
        # Quota logging usunięty - ultra lean mode
        
        return {
            'success': True,
            'added': len(new_channels),
            'existing': len(resolved_channels) - len(new_channels),
            'total': len(self.channels_config['channels'][room_name]),
            'quota_used': 0  # Ultra lean mode
        }
    
    def process_sledz_command(self, room_name, message):
        """Przetwarza komendę !śledź"""
        # Analizuj linki
        analysis = self.analyze_links_cost(message)
        
        # Dodaj kanały
        result = self.add_channels_to_room(room_name, analysis)
        
        # Dodaj informacje o odrzuconych linkach
        if analysis['forbidden']:
            result['forbidden_links'] = '\n'.join(analysis['forbidden'])
        
        return result
    
    def get_room_channels(self, room_name):
        """Pobiera kanały dla konkretnego pokoju"""
        return self.channels_config.get('channels', {}).get(room_name, [])
    
    def get_all_rooms(self):
        """Pobiera wszystkie pokoje"""
        return list(self.channels_config.get('channels', {}).keys()) 