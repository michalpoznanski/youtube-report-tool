#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 SLEDZ SYSTEM V3 FIXED - TYLKO @handle dozwolone
==================================================

Funkcje:
- Akceptuje TYLKO linki @handle
- Odrzuca wszystkie inne formaty
- Edukuje użytkownika o poprawnych formatach
"""

import json
import os
import re
from datetime import datetime

class SledzSystemV3:
    """System !śledź akceptujący TYLKO @handle"""
    
    def __init__(self, channels_config_path="channels_config.json", api_key=None, quota_manager=None):
        self.channels_config_path = channels_config_path
        self.api_key = api_key
        self.quota_manager = quota_manager
        self.channels_config = {}
        
        # Każdy @handle kosztuje 1 quota
        self.HANDLE_COST = 1
        
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
    
    def analyze_links_cost(self, message):
        """Analizuje koszty - TYLKO @handle dozwolone"""
        
        # Wyciągnij linki
        all_links = self.extract_youtube_links(message)
        
        if not all_links:
            return {
                'success': False,
                'error': 'Nie znaleziono linków YouTube',
                'total_cost': 0
            }
        
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
    
    def _analyze_single_link(self, link):
        """Analizuje pojedynczy link - @handle i Channel ID dozwolone!"""
        
        link = link.strip()
        channel_id_pattern = re.compile(r'UC[a-zA-Z0-9_-]{22}')
        
        # Channel ID - 0 quota (DARMOWE!)
        if channel_id_pattern.fullmatch(link) or 'youtube.com/channel/UC' in link:
            return {
                'link': link,
                'type': 'channel_id',
                'cost': 0,
                'description': 'Channel ID - darmowe'
            }
        
        # @handle - 1 quota
        if '@' in link and ('youtube.com/@' in link or link.startswith('@')):
            return {
                'link': link,
                'type': 'handle', 
                'cost': self.HANDLE_COST,
                'description': '@handle - akceptowany format'
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
    
    def create_forbidden_links_embed(self, analysis):
        """Tworzy embed z informacją o niedozwolonych linkach"""
        
        data = analysis['analysis']
        
        embed = {
            'title': '🚫 **NIEDOZWOLONE FORMATY LINKÓW**',
            'description': 'Użyj **TYLKO** linków @handle w formacie:\n`https://www.youtube.com/@NazwaKanału`',
            'color': 0xff0000,
            'fields': []
        }
        
        # Lista błędów
        if data['errors']:
            error_list = []
            for error in data['errors'][:5]:  # Pokaż max 5 błędów
                short_link = error['link'][:50] + "..." if len(error['link']) > 50 else error['link']
                error_list.append(f"• {short_link}")
                error_list.append(f"  {error['error']}")
            
            if len(data['errors']) > 5:
                error_list.append(f"... i {len(data['errors']) - 5} więcej")
            
            embed['fields'].append({
                'name': f'❌ **Problematyczne linki** ({data["forbidden_links"]})',
                'value': '\n'.join(error_list),
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
            'name': '💡 **Jak znaleźć @handle?**',
            'value': '1. Idź na stronę kanału YouTube\n2. Skopiuj adres z paska przeglądarki\n3. Upewnij się że zawiera `/@nazwa`',
            'inline': False
        })
        
        return embed
    
    def create_success_embed(self, analysis):
        """Tworzy embed z sukcesem - tylko @handle"""
        
        data = analysis['analysis']
        
        embed = {
            'title': '✅ **KANAŁY ZAAKCEPTOWANE**',
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
    
    def extract_youtube_links(self, message):
        """Wyciąga wszystkie potencjalne linki YouTube"""
        
        patterns = [
            r'https?://(?:www\.)?youtube\.com/[^\s]+',
            r'https?://youtu\.be/[^\s]+',
            r'@[a-zA-Z0-9._-]+',
            r'UC[a-zA-Z0-9_-]{22}'
        ]
        
        all_links = []
        for pattern in patterns:
            all_links.extend(re.findall(pattern, message))
        
        return all_links

# DEMO TESTOWY
if __name__ == "__main__":
    sledz = SledzSystemV3()
    
    print("🔧 SLEDZ SYSTEM V3 - TYLKO @HANDLE")
    print("=" * 40)
    
    test_message = """
    https://www.youtube.com/@pudelektv
    @StanSkupienia.Podcast
    UCShUU9VW-unGNHC-3XMUSmQ
    https://youtube.com/watch?v=abc
    """
    
    analysis = sledz.analyze_links_cost(test_message)
    
    if analysis['success']:
        print("✅ ZAAKCEPTOWANE")
        print(f"Koszt: {analysis['analysis']['total_cost']} quota")
    else:
        print("❌ ODRZUCONE")
        print(f"Błąd: {analysis['error']}")
        print(f"Błędnych linków: {analysis['analysis']['forbidden_links']}") 