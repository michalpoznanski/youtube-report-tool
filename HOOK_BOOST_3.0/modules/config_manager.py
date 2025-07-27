#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONFIG MANAGER - HOOK BOOST 3.0
===============================

Zarządzanie konfiguracją i strukturami katalogów.
"""

import os
import json
from datetime import datetime

class ConfigManager:
    """Zarządzanie konfiguracją Hook Boost 3.0"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.raw_data_dir = os.path.join(self.data_dir, 'raw_data')
        self.channels_config_path = os.path.join(self.data_dir, 'channels_config.json')
        
        print(f"📁 ConfigManager: {self.base_dir}")
    
    def ensure_directories(self):
        """Tworzy wymagane katalogi"""
        directories = [
            self.data_dir,
            self.raw_data_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ Utworzono katalog: {directory}")
    
    def get_today_raw_data_dir(self):
        """Zwraca ścieżkę do katalogu raw_data dla dzisiejszej daty"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_dir = os.path.join(self.raw_data_dir, today)
        
        if not os.path.exists(today_dir):
            os.makedirs(today_dir)
            print(f"✅ Utworzono katalog dzienny: {today_dir}")
        
        return today_dir
    
    def load_channels_config(self):
        """Ładuje konfigurację kanałów"""
        if os.path.exists(self.channels_config_path):
            try:
                with open(self.channels_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Błąd ładowania konfiguracji: {e}")
        
        # Domyślna konfiguracja
        return {"channels": {}}
    
    def save_channels_config(self, config):
        """Zapisuje konfigurację kanałów"""
        try:
            with open(self.channels_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu konfiguracji: {e}")
            return False
    
    def get_room_channels(self, room_name):
        """Pobiera kanały dla konkretnego pokoju"""
        config = self.load_channels_config()
        return config.get('channels', {}).get(room_name, [])
    
    def add_channels_to_room(self, room_name, channel_ids):
        """Dodaje kanały do pokoju"""
        config = self.load_channels_config()
        
        if 'channels' not in config:
            config['channels'] = {}
        
        if room_name not in config['channels']:
            config['channels'][room_name] = []
        
        # Dodaj nowe kanały (bez duplikatów)
        existing = set(config['channels'][room_name])
        new_channels = []
        
        for channel_id in channel_ids:
            if channel_id not in existing:
                config['channels'][room_name].append(channel_id)
                new_channels.append(channel_id)
        
        # Zapisz konfigurację
        if self.save_channels_config(config):
            return {
                'success': True,
                'added': len(new_channels),
                'existing': len(channel_ids) - len(new_channels),
                'total': len(config['channels'][room_name])
            }
        else:
            return {
                'success': False,
                'error': 'Błąd zapisu konfiguracji'
            } 