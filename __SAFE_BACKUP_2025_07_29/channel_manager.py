#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📺 CHANNEL MANAGER - ULTRA LEAN
==============================

Prosty manager kanałów YouTube:
- Multi-room support
- Ekstraktowanie linków z wiadomości
- Zapis do channels_config.json
- Bez quota managera

AUTOR: Hook Boost V3 - Fresh Ultra Lean
WERSJA: 3.0.0 (2025-01-27)
"""

import os
import json
import re
from typing import List, Dict, Any

class ChannelManager:
    """Ultra prosty manager kanałów YouTube"""
    
    def __init__(self):
        self.config_file = "channels_config.json"
        
        # YouTube patterns
        self.patterns = {
            'handle': re.compile(r'@([a-zA-Z0-9_.-]+)'),
            'channel_url': re.compile(r'youtube\.com/channel/([a-zA-Z0-9_-]+)'),
            'handle_url': re.compile(r'youtube\.com/@([a-zA-Z0-9_.-]+)'),
            'channel_id': re.compile(r'^UC[a-zA-Z0-9_-]{22}$')
        }
        
        print("📺 ChannelManager V3 initialized")
    
    def _load_config(self) -> Dict[str, List[str]]:
        """Ładuje konfigurację kanałów"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Błąd ładowania config: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, List[str]]) -> bool:
        """Zapisuje konfigurację kanałów"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu config: {e}")
            return False
    
    def extract_channels(self, text: str) -> List[str]:
        """Ekstraktuje kanały z tekstu"""
        channels = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle @nazwa
            if self.patterns['handle'].search(line):
                handles = self.patterns['handle'].findall(line)
                for handle in handles:
                    channels.append(f"@{handle}")
            
            # Channel URL
            elif self.patterns['channel_url'].search(line):
                ids = self.patterns['channel_url'].findall(line)
                channels.extend(ids)
            
            # Handle URL
            elif self.patterns['handle_url'].search(line):
                handles = self.patterns['handle_url'].findall(line)
                for handle in handles:
                    channels.append(f"@{handle}")
            
            # Direct Channel ID
            elif self.patterns['channel_id'].match(line):
                channels.append(line)
        
        return list(set(channels))  # Usuń duplikaty
    
    def get_channels(self, room: str) -> List[str]:
        """Pobiera kanały dla pokoju"""
        config = self._load_config()
        return config.get(room, [])
    
    def add_channels(self, room: str, text: str) -> Dict[str, Any]:
        """Dodaje kanały do pokoju"""
        try:
            # Ekstraktuj kanały
            new_channels = self.extract_channels(text)
            
            if not new_channels:
                return {
                    'success': False,
                    'error': 'Nie znaleziono żadnych kanałów YouTube'
                }
            
            # Załaduj config
            config = self._load_config()
            if room not in config:
                config[room] = []
            
            # Sprawdź co jest nowe
            existing = set(config[room])
            to_add = [ch for ch in new_channels if ch not in existing]
            already_there = [ch for ch in new_channels if ch in existing]
            
            # Dodaj nowe
            config[room].extend(to_add)
            
            # Zapisz
            if self._save_config(config):
                return {
                    'success': True,
                    'added': len(to_add),
                    'existing': len(already_there),
                    'total': len(config[room])
                }
            else:
                return {
                    'success': False,
                    'error': 'Błąd zapisu konfiguracji'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Błąd: {str(e)}'
            } 