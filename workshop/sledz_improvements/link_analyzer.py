#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 LINK ANALYZER - Rozpoznawanie Channel ID z linków YouTube
============================================================

Cel: Wyciągnąć Channel ID z linków bez zapytań API gdzie to możliwe
"""

import re
from urllib.parse import urlparse, parse_qs

class LinkAnalyzer:
    """Analizuje linki YouTube i próbuje wyciągnąć Channel ID bez API"""
    
    def __init__(self):
        # Wzorce Channel ID (zawsze zaczynają się od UC i mają 24 znaki)
        self.channel_id_pattern = re.compile(r'UC[a-zA-Z0-9_-]{22}')
        
        # Wzorce @handle (nowy format YouTube)
        self.handle_pattern = re.compile(r'@[a-zA-Z0-9._-]+')
        
        # Wzorce /c/ (stary format niestandardowych nazw)
        self.custom_name_pattern = re.compile(r'/c/([a-zA-Z0-9._-]+)')
        
        # Wzorce /user/ (bardzo stary format)
        self.user_pattern = re.compile(r'/user/([a-zA-Z0-9._-]+)')
    
    def analyze_link(self, link):
        """Analizuje pojedynczy link i określa jak go przetworzyć"""
        
        # Usuń białe znaki
        link = link.strip()
        
        result = {
            'original_link': link,
            'type': 'unknown',
            'extracted_id': None,
            'needs_api': True,
            'api_cost': 0,
            'confidence': 'low'
        }
        
        # 1. Sprawdź czy to już gotowy Channel ID
        if self.channel_id_pattern.fullmatch(link):
            result.update({
                'type': 'channel_id',
                'extracted_id': link,
                'needs_api': False,
                'api_cost': 0,
                'confidence': 'high'
            })
            return result
        
        # 2. Sprawdź czy link zawiera Channel ID
        channel_id_match = self.channel_id_pattern.search(link)
        if channel_id_match:
            result.update({
                'type': 'channel_url_with_id',
                'extracted_id': channel_id_match.group(),
                'needs_api': False,
                'api_cost': 0,
                'confidence': 'high'
            })
            return result
        
        # 3. Sprawdź linki do filmów - może mają Channel ID w parametrach
        if 'youtube.com/watch' in link or 'youtu.be/' in link:
            video_id = self._extract_video_id(link)
            if video_id:
                result.update({
                    'type': 'video_link',
                    'extracted_id': video_id,
                    'needs_api': True,
                    'api_cost': 2,  # videos.list + channels.list
                    'confidence': 'medium'
                })
                return result
        
        # 4. Sprawdź @handle
        if '@' in link:
            handle_match = self.handle_pattern.search(link)
            if handle_match:
                result.update({
                    'type': 'handle',
                    'extracted_id': handle_match.group(),
                    'needs_api': True,
                    'api_cost': 1,  # channels.list (forUsername)
                    'confidence': 'high'
                })
                return result
        
        # 5. Sprawdź /c/ (kosztowne!)
        if '/c/' in link:
            custom_match = self.custom_name_pattern.search(link)
            if custom_match:
                result.update({
                    'type': 'custom_name',
                    'extracted_id': custom_match.group(1),
                    'needs_api': True,
                    'api_cost': 100,  # search.list (bardzo drogie!)
                    'confidence': 'low'
                })
                return result
        
        # 6. Sprawdź /user/ (stary format)
        if '/user/' in link:
            user_match = self.user_pattern.search(link)
            if user_match:
                result.update({
                    'type': 'username',
                    'extracted_id': user_match.group(1),
                    'needs_api': True,
                    'api_cost': 1,  # channels.list (forUsername)
                    'confidence': 'medium'
                })
                return result
        
        # 7. Nierozpoznany format
        result.update({
            'type': 'unknown',
            'api_cost': 100,  # Będzie wymagać search
            'confidence': 'very_low'
        })
        
        return result
    
    def _extract_video_id(self, link):
        """Wyciąga Video ID z linku YouTube"""
        
        # youtube.com/watch?v=VIDEO_ID
        if 'youtube.com/watch' in link:
            parsed = urlparse(link)
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                return query_params['v'][0]
        
        # youtu.be/VIDEO_ID
        elif 'youtu.be/' in link:
            parsed = urlparse(link)
            return parsed.path.lstrip('/')
        
        return None
    
    def analyze_batch(self, links):
        """Analizuje wiele linków jednocześnie"""
        
        results = []
        total_cost = 0
        
        for link in links:
            if link.strip():  # Pomiń puste linki
                analysis = self.analyze_link(link)
                results.append(analysis)
                total_cost += analysis['api_cost']
        
        return {
            'results': results,
            'total_api_cost': total_cost,
            'free_operations': len([r for r in results if r['api_cost'] == 0]),
            'costly_operations': len([r for r in results if r['api_cost'] >= 100])
        }
    
    def generate_optimization_tips(self, batch_analysis):
        """Generuje wskazówki jak zoptymalizować koszty"""
        
        tips = []
        
        if batch_analysis['costly_operations'] > 0:
            tips.append("⚠️ Wykryto kosztowne operacje (/c/ linki)")
            tips.append("💡 Użyj @handle zamiast /c/nazwa")
        
        if batch_analysis['total_api_cost'] > 50:
            tips.append("💰 Wysokie koszty quota!")
            tips.append("🎯 Preferuj linki z Channel ID")
        
        free_ratio = batch_analysis['free_operations'] / len(batch_analysis['results']) if batch_analysis['results'] else 0
        if free_ratio > 0.5:
            tips.append("✅ Większość operacji darmowych!")
        
        return tips

# DEMO ANALIZY
if __name__ == "__main__":
    analyzer = LinkAnalyzer()
    
    test_links = [
        "UCShUU9VW-unGNHC-3XMUSmQ",  # Channel ID
        "https://youtube.com/channel/UCShUU9VW-unGNHC-3XMUSmQ",  # Channel URL
        "@swiatgwiazd",  # Handle
        "https://youtube.com/@swiatgwiazd",  # Handle URL
        "https://youtube.com/watch?v=dQw4w9WgXcQ",  # Video
        "https://youtube.com/c/swiatgwiazd",  # Custom name (drogie!)
        "https://youtube.com/user/starzykanał"  # Username
    ]
    
    print("🔍 ANALIZA RÓŻNYCH TYPÓW LINKÓW")
    print("=" * 50)
    
    for link in test_links:
        analysis = analyzer.analyze_link(link)
        print(f"\n📋 Link: {link}")
        print(f"   Typ: {analysis['type']}")
        print(f"   Wyciągnięto: {analysis['extracted_id']}")
        print(f"   Potrzebuje API: {analysis['needs_api']}")
        print(f"   💰 Koszt: {analysis['api_cost']} quota")
        print(f"   🎯 Pewność: {analysis['confidence']}")
    
    # Analiza wsadowa
    batch = analyzer.analyze_batch(test_links)
    print(f"\n📊 PODSUMOWANIE WSADOWE:")
    print(f"   Łączny koszt: {batch['total_api_cost']} quota")
    print(f"   Darmowe operacje: {batch['free_operations']}")
    print(f"   Kosztowne operacje: {batch['costly_operations']}")
    
    # Wskazówki
    tips = analyzer.generate_optimization_tips(batch)
    if tips:
        print(f"\n💡 WSKAZÓWKI:")
        for tip in tips:
            print(f"   {tip}") 