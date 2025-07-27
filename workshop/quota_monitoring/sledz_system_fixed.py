#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 SLEDZ SYSTEM - PRODUKCJA FIXED
=================================

System dodawania kanałów z POPRAWNYM monitorowaniem quota:
- @handle (1 quota) - łatwe do znalezienia
- Channel ID (0 quota) - darmowe!
- Odrzuca wszystkie inne formaty (filmy, /c/, /user/)
- PRAWIDŁOWE logowanie do QuotaManager

AUTOR: Hook Boost V2 - Warsztat Fix
WERSJA: 3.1 (Fixed quota logging)
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional

class SledzSystem:
    """System !śledź z POPRAWNYM monitorowaniem quota"""
    
    def __init__(self, channels_config_path="channels_config.json", api_key=None):
        self.channels_config_path = channels_config_path
        self.api_key = api_key
        self.channels_config = {}
        
        # Koszty quota
        self.HANDLE_COST = 1  # @handle - 1 quota
        self.CHANNEL_ID_COST = 0  # Channel ID - darmowe
        
        # Inicjalizuj QuotaManager jeśli mamy API
        self.quota_manager = None
        if api_key:
            try:
                from quota_manager import QuotaManager
                self.quota_manager = QuotaManager(api_key)
                print("✅ QuotaManager połączony z SledzSystem")
            except ImportError:
                print("⚠️ QuotaManager niedostępny - quota nie będzie monitorowane")
        
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
            error_msg = '❌ Nieznany format - użyj @handle lub Channel ID'
        
        return {
            'link': link,
            'type': 'forbidden',
            'cost': 0,
            'description': error_msg,
            'error': True
        }
    
    def analyze_links_cost(self, message):
        """Analizuje koszty linków"""
        
        # Wyciągnij wszystkie linki
        lines = message.strip().split('\n')
        all_links = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                all_links.append(line)
        
        if not all_links:
            return {
                'success': False,
                'error': 'Nie znaleziono żadnych linków',
                'analysis': None
            }
        
        # Analizuj każdy link
        analysis = {
            'total_links': len(all_links),
            'valid_handles': 0,
            'valid_channel_ids': 0,
            'forbidden_links': 0,
            'total_cost': 0,
            'details': [],
            'errors': []
        }
        
        for link in all_links:
            link_analysis = self._analyze_single_link(link)
            analysis['details'].append(link_analysis)
            
            if link_analysis.get('error'):
                analysis['forbidden_links'] += 1
                analysis['errors'].append({
                    'link': link,
                    'error': link_analysis['description']
                })
            else:
                analysis['total_cost'] += link_analysis['cost']
                if link_analysis['type'] == 'handle':
                    analysis['valid_handles'] += 1
                elif link_analysis['type'] == 'channel_id':
                    analysis['valid_channel_ids'] += 1
        
        # Jeśli są błędne linki, zwróć błąd
        if analysis['forbidden_links'] > 0:
            return {
                'success': False,
                'error': 'Znaleziono niedozwolone formaty linków',
                'analysis': analysis
            }
        
        return {
            'success': True,
            'analysis': analysis
        }
    
    def _resolve_channel_id(self, link_data):
        """Rozwiązuje link do Channel ID z POPRAWNYM logowaniem quota"""
        
        if link_data['type'] == 'channel_id':
            # Wyciągnij Channel ID - DARMOWE
            if link_data['link'].startswith('UC'):
                return link_data['link']
            else:
                # Z URL typu youtube.com/channel/UC...
                match = re.search(r'UC[a-zA-Z0-9_-]{22}', link_data['link'])
                return match.group() if match else None
        
        elif link_data['type'] == 'handle':
            # Wyciągnij handle i zapytaj API
            handle = link_data['link']
            if 'youtube.com/@' in handle:
                handle = handle.split('youtube.com/@')[1]
            elif handle.startswith('@'):
                handle = handle[1:]
            
            # API call - channels().list() z forUsername - 1 quota
            try:
                url = "https://www.googleapis.com/youtube/v3/channels"
                params = {
                    'part': 'id',
                    'forUsername': handle,
                    'key': self.api_key
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # POPRAWNE logowanie quota: (operation_type, params, actual_cost, success)
                if self.quota_manager:
                    self.quota_manager.log_operation(
                        'channels_list',
                        {'handle': handle, 'operation': 'sledz_resolve_handle'},
                        1,  # actual_cost = 1 quota
                        True  # success = True
                    )
                    print(f"✅ Zalogowano 1 quota za @handle: {handle}")
                
                if data.get('items'):
                    return data['items'][0]['id']
                else:
                    # Może to jest handle nowego typu - spróbuj przez search
                    return self._search_channel_by_handle(handle)
                    
            except Exception as e:
                print(f"❌ Błąd resolving handle {handle}: {e}")
                
                # Loguj niepowodzenie
                if self.quota_manager:
                    self.quota_manager.log_operation(
                        'channels_list',
                        {'handle': handle, 'operation': 'sledz_resolve_handle', 'error': str(e)},
                        1,  # actual_cost = 1 quota (było wydane mimo błędu)
                        False  # success = False
                    )
                
                return None
        
        return None
    
    def _search_channel_by_handle(self, handle):
        """Szuka kanału przez handle używając search API z POPRAWNYM logowaniem"""
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'id',
                'q': f'@{handle}',
                'type': 'channel',
                'maxResults': 1,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # POPRAWNE logowanie quota: search kosztuje 100!
            if self.quota_manager:
                self.quota_manager.log_operation(
                    'search',
                    {'handle': handle, 'operation': 'sledz_search_handle'},
                    100,  # actual_cost = 100 quota
                    True  # success = True
                )
                print(f"⚠️ Zalogowano 100 quota za search: {handle}")
            
            if data.get('items'):
                return data['items'][0]['id']['channelId']
                
        except Exception as e:
            print(f"❌ Błąd search handle {handle}: {e}")
            
            # Loguj niepowodzenie search
            if self.quota_manager:
                self.quota_manager.log_operation(
                    'search',
                    {'handle': handle, 'operation': 'sledz_search_handle', 'error': str(e)},
                    100,  # actual_cost = 100 quota (było wydane mimo błędu)
                    False  # success = False
                )
        
        return None
    
    def add_channels_to_room(self, room_name, links_analysis):
        """Dodaje kanały do pokoju"""
        
        if room_name not in self.channels_config['channels']:
            self.channels_config['channels'][room_name] = []
        
        room_channels = set(self.channels_config['channels'][room_name])
        new_channels = []
        already_tracked = []
        quota_used = 0
        
        for link_data in links_analysis['details']:
            if link_data.get('error'):
                continue
                
            # Resolve do Channel ID (tu będzie logowanie quota)
            channel_id = self._resolve_channel_id(link_data)
            quota_used += link_data['cost']  # Przewidywany koszt
            
            if not channel_id:
                print(f"❌ Nie udało się resolve: {link_data['link']}")
                continue
            
            if channel_id in room_channels:
                already_tracked.append(channel_id)
            else:
                room_channels.add(channel_id)
                new_channels.append(channel_id)
        
        # Zapisz zmiany
        self.channels_config['channels'][room_name] = list(room_channels)
        self._save_config()
        
        return {
            'new_channels': new_channels,
            'already_tracked': already_tracked,
            'total_in_room': len(room_channels),
            'quota_used': quota_used  # To jest przewidywany koszt, rzeczywisty jest w log_operation
        }
    
    def process_sledz_command(self, room_name, message):
        """Główna funkcja przetwarzania komendy !śledź z monitorowaniem quota"""
        
        print(f"🔍 Przetwarzam !śledź dla pokoju: {room_name}")
        
        # Analizuj koszty
        cost_analysis = self.analyze_links_cost(message)
        
        if not cost_analysis['success']:
            return {
                'success': False,
                'error': cost_analysis['error'],
                'analysis': cost_analysis['analysis'],
                'quota_cost': 0
            }
        
        analysis = cost_analysis['analysis']
        print(f"📊 Analiza: {analysis['valid_handles']} @handle, {analysis['valid_channel_ids']} Channel ID")
        
        # Dodaj kanały (tu będzie rzeczywiste logowanie quota)
        add_result = self.add_channels_to_room(room_name, analysis)
        
        print(f"✅ Dodano {len(add_result['new_channels'])} nowych kanałów")
        
        return {
            'success': True,
            'add_result': add_result,
            'quota_cost': add_result['quota_used'],
            'analysis': analysis
        }
    
    def get_room_channels(self, room_name):
        """Zwraca kanały dla pokoju"""
        return self.channels_config['channels'].get(room_name, [])
    
    def get_all_rooms(self):
        """Zwraca wszystkie pokoje"""
        return list(self.channels_config['channels'].keys())

# ===== DISCORD EMBEDS =====

def create_forbidden_links_embed(data):
    """Tworzy embed dla błędnych linków"""
    embed = {
        'title': '❌ **NIEDOZWOLONE FORMATY LINKÓW**',
        'description': 'Wykryto linki w nieprawidłowym formacie',
        'color': 0xff0000,
        'fields': []
    }
    
    # Błędy
    if data['errors']:
        error_list = '\n'.join([f"• {err['error']}" for err in data['errors'][:3]])
        if len(data['errors']) > 3:
            error_list += f"\n... i {len(data['errors'])-3} więcej błędów"
        
        embed['fields'].append({
            'name': '🚫 **Wykryte problemy**',
            'value': f"```\n{error_list}\n```",
            'inline': False
        })
    
    # Przykłady poprawnych formatów
    embed['fields'].append({
        'name': '✅ **Poprawne formaty**',
        'value': '```\n@handle (1 quota):\nhttps://www.youtube.com/@pudelektv\n@StanSkupienia.Podcast\n\nChannel ID (0 quota):\nUCShUU9VW-unGNHC-3XMUSmQ\n```',
        'inline': False
    })
    
    # Instrukcje
    embed['fields'].append({
        'name': '💡 **Jak znaleźć @handle**',
        'value': '1. Wejdź na kanał YouTube\n2. Skopiuj link z paska adresu\n3. Sprawdź czy zawiera `@nazwa`',
        'inline': False
    })
    
    return embed

def create_success_embed(data, room_name):
    """Tworzy embed dla udanego dodania kanałów"""
    embed = {
        'title': '✅ **KANAŁY DODANE**',
        'description': f'📍 **Pokój:** #{room_name}',
        'color': 0x00ff00,
        'fields': []
    }
    
    # Podsumowanie
    embed['fields'].append({
        'name': '📊 **Wyniki**',
        'value': f"```\n@handle: {data['valid_handles']} (×1 quota)\nChannel ID: {data['valid_channel_ids']} (×0 quota)\nKoszt łączny: {data['total_cost']} quota\n```",
        'inline': False
    })
    
    # Koszt breakdown
    cost_breakdown = []
    if data['valid_handles'] > 0:
        cost_breakdown.append(f"{data['valid_handles']} @handle × 1 = {data['valid_handles']}")
    if data['valid_channel_ids'] > 0:
        cost_breakdown.append(f"{data['valid_channel_ids']} Channel ID × 0 = 0")
    
    embed['fields'].append({
        'name': '💰 **Koszt**',
        'value': f"```\n{' + '.join(cost_breakdown)} = {data['total_cost']} quota\n```",
        'inline': False
    })
    
    return embed 