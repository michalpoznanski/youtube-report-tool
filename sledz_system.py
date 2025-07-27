#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 SLEDZ SYSTEM - ULTRA LEAN VERSION
===================================

Ultra-lekki system śledzenia kanałów YouTube:
- Multi-room support (każdy pokój Discord = osobna kategoria)
- Bez quota managera - oszczędzamy na monitoringu
- Proste dodawanie kanałów przez !śledź
- Zapisywanie do channels_config.json

AUTOR: Hook Boost V2 - Ultra Lean Edition
WERSJA: 3.0 (Railway Ready)
"""

import os
import json
import re
import requests
from datetime import datetime
from typing import List, Dict, Any

class SledzSystem:
    """Ultra lean system śledzenia kanałów YouTube"""
    
    def __init__(self, api_key: str = None):
        """
        Inicjalizacja systemu śledzenia
        
        Args:
            api_key: YouTube Data API key (opcjonalny dla niektórych operacji)
        """
        self.api_key = api_key
        self.config_file = "channels_config.json"
        
        # YouTube URL patterns
        self.youtube_patterns = {
            'handle': re.compile(r'@([a-zA-Z0-9_.-]+)'),
            'channel_url': re.compile(r'youtube\.com/channel/([a-zA-Z0-9_-]+)'),
            'user_url': re.compile(r'youtube\.com/user/([a-zA-Z0-9_-]+)'),
            'custom_url': re.compile(r'youtube\.com/c/([a-zA-Z0-9_.-]+)'),
            'handle_url': re.compile(r'youtube\.com/@([a-zA-Z0-9_.-]+)'),
            'channel_id': re.compile(r'^UC[a-zA-Z0-9_-]{22}$')
        }
        
        print("✅ SledzSystem Ultra Lean - initialized")
    
    def _load_channels_config(self) -> Dict[str, List[str]]:
        """Ładuje konfigurację kanałów z pliku"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"📁 Loaded {len(config)} rooms from config")
                    return config
            else:
                print("📁 Creating new channels_config.json")
                return {}
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def _save_channels_config(self, config: Dict[str, List[str]]) -> bool:
        """Zapisuje konfigurację kanałów do pliku"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved config with {len(config)} rooms")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def get_room_channels(self, room_name: str) -> List[str]:
        """Pobiera listę kanałów dla danego pokoju"""
        config = self._load_channels_config()
        channels = config.get(room_name, [])
        print(f"📺 Room '{room_name}' has {len(channels)} channels")
        return channels
    
    def extract_youtube_info(self, text: str) -> Dict[str, Any]:
        """Ekstrahuje informacje o kanałach YouTube z tekstu"""
        results = {
            'handles': [],
            'channel_ids': [],
            'channel_urls': [],
            'user_urls': [],
            'custom_urls': [],
            'handle_urls': [],
            'direct_ids': [],
            'forbidden_links': [],
            'unprocessed_links': []
        }
        
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Sprawdź wzorce YouTube
            if self.youtube_patterns['handle'].search(line):
                handles = self.youtube_patterns['handle'].findall(line)
                results['handles'].extend(handles)
                
            elif self.youtube_patterns['channel_url'].search(line):
                ids = self.youtube_patterns['channel_url'].findall(line)
                results['channel_urls'].extend(ids)
                
            elif self.youtube_patterns['user_url'].search(line):
                users = self.youtube_patterns['user_url'].findall(line)
                results['user_urls'].extend(users)
                
            elif self.youtube_patterns['custom_url'].search(line):
                customs = self.youtube_patterns['custom_url'].findall(line)
                results['custom_urls'].extend(customs)
                
            elif self.youtube_patterns['handle_url'].search(line):
                handle_urls = self.youtube_patterns['handle_url'].findall(line)
                results['handle_urls'].extend(handle_urls)
                
            elif self.youtube_patterns['channel_id'].match(line):
                results['direct_ids'].append(line)
                
            elif 'youtube.com' in line and ('shorts' in line or 'watch' in line):
                results['forbidden_links'].append(line)
                
            elif 'youtube.com' in line:
                results['unprocessed_links'].append(line)
        
        return results
    
    def resolve_to_channel_ids(self, youtube_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rozwiązuje różne formaty YouTube na Channel ID (ultra lean - bez API)"""
        resolved = {
            'channel_ids': [],
            'failed_resolves': [],
            'api_quota_used': 0
        }
        
        # Direct channel IDs
        resolved['channel_ids'].extend(youtube_info['direct_ids'])
        resolved['channel_ids'].extend(youtube_info['channel_urls'])
        
        # Handles - dodaj jako handle (bez resolving w ultra lean mode)
        for handle in youtube_info['handles'] + youtube_info['handle_urls']:
            # W ultra lean mode zapisujemy handle jako placeholder
            resolved['channel_ids'].append(f"@{handle}")
        
        # User URLs i custom URLs - też jako placeholder
        for user in youtube_info['user_urls']:
            resolved['failed_resolves'].append(f"user/{user} - requires API resolution")
            
        for custom in youtube_info['custom_urls']:
            resolved['failed_resolves'].append(f"c/{custom} - requires API resolution")
        
        return resolved
    
    def add_channels_to_room(self, room_name: str, channel_ids: List[str]) -> Dict[str, Any]:
        """Dodaje kanały do pokoju"""
        config = self._load_channels_config()
        
        if room_name not in config:
            config[room_name] = []
        
        existing_channels = set(config[room_name])
        new_channels = []
        already_tracked = []
        
        for channel_id in channel_ids:
            if channel_id not in existing_channels:
                config[room_name].append(channel_id)
                new_channels.append(channel_id)
            else:
                already_tracked.append(channel_id)
        
        if self._save_channels_config(config):
            return {
                'success': True,
                'new_channels': new_channels,
                'already_tracked': already_tracked,
                'total_in_room': len(config[room_name])
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save config'
            }
    
    def process_sledz_command(self, room_name: str, message: str) -> Dict[str, Any]:
        """Przetwarza komendę !śledź dla danego pokoju"""
        try:
            # Ekstraktuj informacje YouTube
            youtube_info = self.extract_youtube_info(message)
            
            # Policz wszystkie znalezione linki
            total_found = (len(youtube_info['handles']) + 
                          len(youtube_info['channel_urls']) + 
                          len(youtube_info['user_urls']) + 
                          len(youtube_info['custom_urls']) + 
                          len(youtube_info['handle_urls']) + 
                          len(youtube_info['direct_ids']))
            
            if total_found == 0:
                return {
                    'success': False,
                    'error': 'Nie znaleziono żadnych linków YouTube',
                    'analysis': youtube_info
                }
            
            # Rozwiąż na Channel ID
            resolved = self.resolve_to_channel_ids(youtube_info)
            
            if not resolved['channel_ids']:
                return {
                    'success': False,
                    'error': 'Nie udało się rozwiązać żadnych kanałów na Channel ID',
                    'analysis': {**youtube_info, **resolved}
                }
            
            # Dodaj do pokoju
            add_result = self.add_channels_to_room(room_name, resolved['channel_ids'])
            
            return {
                'success': add_result['success'],
                'analysis': {**youtube_info, **resolved},
                'add_result': add_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Błąd przetwarzania: {str(e)}'
            }

# ===== EMBED CREATORS (ULTRA LEAN) =====

def create_success_embed(analysis: Dict[str, Any], room_name: str) -> Dict[str, Any]:
    """Tworzy dane dla success embed (ultra lean)"""
    total_links = (len(analysis.get('handles', [])) + 
                   len(analysis.get('channel_urls', [])) + 
                   len(analysis.get('direct_ids', [])) + 
                   len(analysis.get('handle_urls', [])))
    
    return {
        'title': '✅ **KANAŁY DODANE**',
        'description': f'Zaktualizowano śledzenie dla pokoju **#{room_name}**',
        'color': 0x00ff00,
        'fields': [
            {
                'name': '📊 **Analiza linków**',
                'value': f'```\nZnalezione linki: {total_links}\nHandles: {len(analysis.get("handles", []))}\nChannel URLs: {len(analysis.get("channel_urls", []))}\nDirect IDs: {len(analysis.get("direct_ids", []))}\n```',
                'inline': False
            }
        ]
    }

def create_forbidden_links_embed(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Tworzy dane dla forbidden links embed"""
    return {
        'title': '❌ **NIEDOZWOLONE LINKI**',
        'description': 'Znaleziono linki do filmów/shorts zamiast kanałów',
        'color': 0xff0000,
        'fields': [
            {
                'name': '🚫 **Problematyczne linki**',
                'value': f'```\n{chr(10).join(analysis.get("forbidden_links", [])[:5])}\n```',
                'inline': False
            },
            {
                'name': '✅ **Rozwiązanie**',
                'value': 'Użyj linków do **kanałów**, nie do konkretnych filmów',
                'inline': False
            }
        ]
    } 