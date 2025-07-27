#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 SLEDZ SYSTEM V3 - Z zabezpieczeniami quota
============================================

Funkcje:
- Analizuje koszty przed wykonaniem
- Pyta o potwierdzenie przy wysokich kosztach
- Pokazuje szczegółowe informacje o quota
- Edukuje użytkownika o kosztach
"""

import json
import os
import re
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class SledzSystemV3:
    """System !śledź z zabezpieczeniami quota"""
    
    def __init__(self, channels_config_path="channels_config.json", api_key=None, quota_manager=None):
        self.channels_config_path = channels_config_path
        self.api_key = api_key
        self.quota_manager = quota_manager
        self.channels_config = {}
        
        # Progi ostrzeżeń quota
        self.QUOTA_WARNING_THRESHOLD = 10  # Ostrzeż przy kosztach > 10
        self.QUOTA_DANGER_THRESHOLD = 50   # Wymagaj potwierdzenia przy > 50
        
        # Wzorce do rozpoznawania linków
        self.channel_id_pattern = re.compile(r'UC[a-zA-Z0-9_-]{22}')
        self.handle_pattern = re.compile(r'@[a-zA-Z0-9._-]+')
        
        self._load_config()
    
    def _load_config(self):
        """Ładuje konfigurację kanałów"""
        try:
            if os.path.exists(self.channels_config_path):
                with open(self.channels_config_path, 'r', encoding='utf-8') as f:
                    self.channels_config = json.load(f)
            
            # Zapewnij strukturę channels
            if 'channels' not in self.channels_config:
                self.channels_config['channels'] = {}
                
        except Exception as e:
            print(f"Błąd ładowania config: {e}")
            self.channels_config = {'channels': {}}
    
    def _save_config(self):
        """Zapisuje konfigurację kanałów"""
        try:
            with open(self.channels_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.channels_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisu config: {e}")
    
    def analyze_links_cost(self, message):
        """Analizuje koszty quota dla podanych linków"""
        
        # Wyciągnij linki
        channel_links, video_links = self.extract_youtube_links(message)
        all_links = channel_links + video_links
        
        if not all_links:
            return {
                'success': False,
                'error': 'Nie znaleziono linków YouTube',
                'total_cost': 0
            }
        
        analysis = {
            'total_links': len(all_links),
            'valid_handles': 0,
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
        """Analizuje pojedynczy link - TYLKO @handle dozwolone!"""
        
        link = link.strip()
        
        # TYLKO @handle - 1 quota
        if '@' in link and ('youtube.com/@' in link or link.startswith('@')):
            return {
                'link': link,
                'type': 'handle', 
                'cost': 1,
                'description': '@handle - akceptowany format'
            }
        
        # WSZYSTKIE INNE FORMATY - ODRZUĆ!
        error_msg = None
        if self.channel_id_pattern.fullmatch(link) or 'youtube.com/channel/UC' in link:
            error_msg = '❌ Channel ID nie jest dozwolony - użyj @handle'
        elif 'youtube.com/watch' in link or 'youtu.be/' in link:
            error_msg = '❌ Linki do filmów nie są dozwolone - użyj @handle kanału'
        elif '/c/' in link:
            error_msg = '❌ Linki /c/ nie są dozwolone - użyj @handle'
        elif '/user/' in link:
            error_msg = '❌ Linki /user/ nie są dozwolone - użyj @handle'
        else:
            error_msg = '❌ Nieznany format - użyj format @handle'
        
        return {
            'link': link,
            'type': 'forbidden',
            'cost': 0,
            'description': error_msg,
            'error': True
        }
    
    def create_cost_analysis_embed(self, analysis):
        """Tworzy embed z analizą kosztów"""
        
        data = analysis['analysis']
        
        # Kolor zależny od kosztu
        if data['total_cost'] == 0:
            color = 0x00ff00  # Zielony
            title = "✅ **ANALIZA KOSZTÓW - DARMOWE**"
        elif data['total_cost'] <= self.QUOTA_WARNING_THRESHOLD:
            color = 0xffa500  # Pomarańczowy  
            title = "⚠️ **ANALIZA KOSZTÓW - NISKIE**"
        elif data['total_cost'] <= self.QUOTA_DANGER_THRESHOLD:
            color = 0xff8c00  # Ciemnopomarańczowy
            title = "🚨 **ANALIZA KOSZTÓW - WYSOKIE**"
        else:
            color = 0xff0000  # Czerwony
            title = "💥 **ANALIZA KOSZTÓW - BARDZO WYSOKIE**"
        
        embed = {
            'title': title,
            'color': color,
            'fields': []
        }
        
        # Podsumowanie typów
        embed['fields'].append({
            'name': '📊 **Typy linków**',
            'value': f"```\n"
                     f"Channel ID: {data['channel_ids']} (×0 quota)\n"
                     f"@handles: {data['handles']} (×1 quota)\n"
                     f"Filmy: {data['videos']} (×2 quota)\n"
                     f"Custom /c/: {data['custom_names']} (×100 quota)\n"
                     f"Nieznane: {data['unknown']} (×100 quota)\n"
                     f"```",
            'inline': True
        })
        
        # Koszt łączny
        embed['fields'].append({
            'name': '💰 **Łączny koszt**',
            'value': f"```\n{data['total_cost']} quota\n```",
            'inline': True
        })
        
        # Rekomendacje
        recommendations = []
        if data['custom_names'] > 0:
            recommendations.append("⚠️ Unikaj linków /c/ - użyj @handle")
        if data['videos'] > 0:
            recommendations.append("💡 Linki kanałów są tańsze niż filmy")
        if data['total_cost'] > 20:
            recommendations.append("🎯 Rozważ podział na mniejsze części")
        
        if recommendations:
            embed['fields'].append({
                'name': '💡 **Rekomendacje**',
                'value': '\n'.join(recommendations),
                'inline': False
            })
        
        return embed
    
    def needs_confirmation(self, total_cost, available_quota=None):
        """Sprawdza czy operacja wymaga potwierdzenia"""
        
        # Zawsze pytaj przy wysokich kosztach
        if total_cost > self.QUOTA_DANGER_THRESHOLD:
            return True, f"Wysokie koszty quota ({total_cost} punktów)"
        
        # Pytaj jeśli zostało mało quota
        if available_quota and total_cost > available_quota * 0.2:  # >20% pozostałego quota
            return True, f"Operacja zużyje {total_cost}/{available_quota} dostępnego quota"
        
        # Pytaj przy średnich kosztach
        if total_cost > self.QUOTA_WARNING_THRESHOLD:
            return True, f"Średnie koszty quota ({total_cost} punktów)"
        
        return False, None
    
    def create_confirmation_embed(self, analysis, reason):
        """Tworzy embed z prośbą o potwierdzenie"""
        
        embed = {
            'title': '❓ **POTWIERDZENIE WYMAGANE**',
            'description': reason,
            'color': 0xff8c00,
            'fields': [
                {
                    'name': '💰 **Koszt operacji**',
                    'value': f"```\n{analysis['analysis']['total_cost']} quota\n```",
                    'inline': True
                },
                {
                    'name': '📊 **Linków do przetworzenia**',
                    'value': f"```\n{analysis['analysis']['total_links']}\n```",
                    'inline': True
                },
                {
                    'name': '❓ **Kontynuować?**',
                    'value': "Użyj `!śledź potwierdzam` aby kontynuować\nlub `!śledź anuluj` aby anulować",
                    'inline': False
                }
            ]
        }
        
        return embed
    
    def create_forbidden_links_embed(self, analysis):
        """Tworzy embed z informacją o niedozwolonych linkach"""
        
        data = analysis['analysis']
        
        embed = {
            'title': '🚫 **NIEDOZWOLONE FORMATY LINKÓW**',
            'description': f'Użyj **TYLKO** linków @handle w formacie:\n`https://www.youtube.com/@NazwaKanału`',
            'color': 0xff0000,
            'fields': []
        }
        
        # Lista błędów
        if data['errors']:
            error_list = []
            for error in data['errors'][:5]:  # Pokaż max 5 błędów
                error_list.append(f"• {error['link']}\n  {error['error']}")
            
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
            'value': '```\nhttps://www.youtube.com/@pudelektv\nhttps://www.youtube.com/@radiozet\n@StanSkupienia.Podcast\n```',
            'inline': False
        })
        
        # Instrukcje
        embed['fields'].append({
            'name': '💡 **Jak znaleźć @handle?**',
            'value': '1. Idź na stronę kanału YouTube\n2. Skopiuj adres z paska przeglądarki\n3. Upewnij się że zawiera `/@nazwa`',
            'inline': False
        })
        
        return embed
    
    def extract_youtube_links(self, message):
        """Wyciąga linki YouTube z wiadomości"""
        
        channel_patterns = [
            r'https?://(?:www\.)?youtube\.com/channel/[^\s]+',
            r'https?://(?:www\.)?youtube\.com/c/[^\s]+', 
            r'https?://(?:www\.)?youtube\.com/@[^\s]+',
            r'https?://(?:www\.)?youtube\.com/user/[^\s]+',
            r'@[a-zA-Z0-9._-]+',
            r'UC[a-zA-Z0-9_-]{22}'
        ]
        
        video_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?[^\s]+',
            r'https?://youtu\.be/[^\s]+'
        ]
        
        channel_links = []
        video_links = []
        
        for pattern in channel_patterns:
            channel_links.extend(re.findall(pattern, message))
        
        for pattern in video_patterns:
            video_links.extend(re.findall(pattern, message))
        
        return channel_links, video_links

# PRZYKŁAD UŻYCIA W BOCIE:

"""
@bot.command(name='śledź')
async def sledz_command(ctx, *, message: str = None):
    try:
        sledz = SledzSystemV3(api_key=YOUTUBE_API_KEY, quota_manager=quota_manager)
        
        # Analiza kosztów
        cost_analysis = sledz.analyze_links_cost(message)
        
        if not cost_analysis['success']:
            await ctx.send(f"❌ {cost_analysis['error']}")
            return
        
        # Sprawdź czy potrzebne potwierdzenie
        available_quota = quota_manager.get_estimated_available_quota() if quota_manager else None
        needs_confirm, reason = sledz.needs_confirmation(
            cost_analysis['analysis']['total_cost'], 
            available_quota
        )
        
        if needs_confirm:
            # Pokaż analizę i poproś o potwierdzenie
            cost_embed = sledz.create_cost_analysis_embed(cost_analysis)
            confirm_embed = sledz.create_confirmation_embed(cost_analysis, reason)
            
            await ctx.send(embed=cost_embed)
            await ctx.send(embed=confirm_embed)
            return
        
        # Wykonaj operację jeśli nie potrzebuje potwierdzenia
        result = sledz.process_sledz_command(ctx.channel.name, message)
        # ... wyświetl wyniki
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD**: {str(e)}")
"""

if __name__ == "__main__":
    print("🔧 Sledz System V3 - Z zabezpieczeniami quota")
    print("   Funkcje:")
    print("   - Analiza kosztów przed wykonaniem")
    print("   - Prośba o potwierdzenie przy wysokich kosztach")
    print("   - Szczegółowe informacje o typach linków")
    print("   - Edukacyjne rekomendacje") 