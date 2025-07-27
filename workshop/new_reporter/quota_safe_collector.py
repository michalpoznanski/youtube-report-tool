#!/usr/bin/env python3
"""
QUOTA-SAFE COLLECTOR - Nowy system zbierania danych YouTube
GŁÓWNY CEL: Zero przepalania quota + dokładne liczenie kosztów

Bezpieczne limity:
- Max 10 kanałów na operację  
- Filtrowanie po datach (tylko ostatnie X dni)
- Pre-check quota przed każdą operacją
- Dokładne szacowanie kosztów
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from quota_manager import QuotaManager


class QuotaSafeCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.quota_manager = QuotaManager(api_key)
        
        # BEZPIECZNE LIMITY
        self.MAX_CHANNELS_PER_RUN = 10
        self.MAX_VIDEOS_PER_CHANNEL = 25  # Zmniejszone z 50
        self.DEFAULT_DAYS_BACK = 7
        
    def estimate_collection_cost(self, channels: list, days: int = 7) -> dict:
        """Dokładne szacowanie kosztów PRZED wykonaniem"""
        
        # Policz typy kanałów
        channel_ids = [ch for ch in channels if ch.startswith('UC') and len(ch) == 24]
        handles = [ch for ch in channels if not (ch.startswith('UC') and len(ch) == 24)]
        
        costs = {
            'channel_resolution': 0,  # Rozwiązywanie handles do IDs
            'video_search': 0,        # Szukanie filmów
            'video_details': 0,       # Szczegóły filmów
            'total': 0
        }
        
        # Koszt rozwiązywania handles (jeśli są)
        if handles:
            # channels().list dla każdego handle = 1 quota each
            costs['channel_resolution'] = len(handles) * 1
        
        # Koszt szukania filmów dla każdego kanału
        # search().list lub playlistItems().list = 1 quota each
        costs['video_search'] = len(channels) * 1
        
        # Koszt szczegółów filmów
        # videos().list może obsłużyć do 50 IDs za 1 quota
        estimated_videos = len(channels) * self.MAX_VIDEOS_PER_CHANNEL
        costs['video_details'] = max(1, estimated_videos // 50)
        
        costs['total'] = sum(costs.values())
        
        return {
            'costs': costs,
            'channels_count': len(channels),
            'estimated_videos': estimated_videos,
            'days_filter': days,
            'safe_to_run': costs['total'] < 1000,  # Bezpieczny limit
            'recommendation': self._get_cost_recommendation(costs['total'])
        }
    
    def _get_cost_recommendation(self, total_cost: int) -> str:
        """Rekomendacja na podstawie kosztu"""
        if total_cost < 100:
            return "🟢 BEZPIECZNE - niski koszt"
        elif total_cost < 500:
            return "🟡 UMIARKOWANE - średni koszt"
        elif total_cost < 1000:
            return "🟠 WYSOKIE - wysoki koszt"
        else:
            return "🔴 NIEBEZPIECZNE - zbyt wysoki koszt"
    
    def can_collect_safely(self, channels: list, days: int = 7) -> dict:
        """Sprawdza czy można bezpiecznie zebrać dane"""
        
        # Sprawdź quota
        quota_summary = self.quota_manager.get_quota_summary()
        remaining_quota = quota_summary['today_remaining']
        
        # Szacuj koszt
        cost_estimate = self.estimate_collection_cost(channels, days)
        
        # Sprawdź limity
        checks = {
            'quota_available': remaining_quota > 0,
            'quota_sufficient': remaining_quota >= cost_estimate['costs']['total'],
            'channels_within_limit': len(channels) <= self.MAX_CHANNELS_PER_RUN,
            'cost_acceptable': cost_estimate['costs']['total'] < 1000
        }
        
        all_safe = all(checks.values())
        
        return {
            'safe': all_safe,
            'checks': checks,
            'remaining_quota': remaining_quota,
            'estimated_cost': cost_estimate['costs']['total'],
            'cost_breakdown': cost_estimate,
            'recommendation': cost_estimate['recommendation']
        }
    
    def filter_channels_by_safety(self, channels: list, max_cost: int = 500) -> dict:
        """Filtruje kanały żeby zmieścić się w bezpiecznym koszcie"""
        
        if not channels:
            return {'safe_channels': [], 'dropped_channels': [], 'estimated_cost': 0}
        
        # Testuj zmniejszające się liczby kanałów
        for i in range(len(channels), 0, -1):
            test_channels = channels[:i]
            cost_estimate = self.estimate_collection_cost(test_channels)
            
            if cost_estimate['costs']['total'] <= max_cost:
                return {
                    'safe_channels': test_channels,
                    'dropped_channels': channels[i:],
                    'estimated_cost': cost_estimate['costs']['total'],
                    'cost_breakdown': cost_estimate
                }
        
        # Żaden kanał nie jest bezpieczny
        return {
            'safe_channels': [],
            'dropped_channels': channels,
            'estimated_cost': 0,
            'message': 'Żaden kanał nie mieści się w bezpiecznym limicie'
        }
    
    def collect_data_safely(self, channels: list, days: int = 7, dry_run: bool = True) -> dict:
        """BEZPIECZNE zbieranie danych z pełną kontrolą quota"""
        
        # Sprawdź bezpieczeństwo
        safety_check = self.can_collect_safely(channels, days)
        
        if not safety_check['safe']:
            return {
                'success': False,
                'error': 'Operacja niebezpieczna dla quota',
                'safety_check': safety_check
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'message': 'DRY RUN - operacja byłaby bezpieczna',
                'safety_check': safety_check,
                'would_collect': f"{len(channels)} kanałów, {days} dni"
            }
        
        # TODO: Rzeczywiste zbieranie danych (następny krok)
        return {
            'success': True,
            'message': 'Rzeczywiste zbieranie - do implementacji',
            'safety_check': safety_check
        }


# TESTY BEZPIECZEŃSTWA
if __name__ == "__main__":
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Brak YOUTUBE_API_KEY")
        exit(1)
    
    collector = QuotaSafeCollector(api_key)
    
    # Test z przykładowymi kanałami
    test_channels = [
        "UC-wh71MEZ4KAx94aZyoG_qg",  # Channel ID
        "UCvHFbkohgX29NhaUtmkzLmg",  # Channel ID  
        "radiozet"                   # Handle
    ]
    
    print("🔍 QUOTA-SAFE COLLECTOR - TESTY")
    print("=" * 40)
    
    # Test 1: Szacowanie kosztów
    cost_estimate = collector.estimate_collection_cost(test_channels, 7)
    print(f"💰 Szacowany koszt: {cost_estimate['costs']['total']} quota")
    print(f"📊 Breakdown: {cost_estimate['costs']}")
    print(f"🎯 Rekomendacja: {cost_estimate['recommendation']}")
    
    # Test 2: Sprawdzenie bezpieczeństwa
    safety = collector.can_collect_safely(test_channels, 7)
    print(f"\n🛡️ Bezpieczeństwo: {'✅ SAFE' if safety['safe'] else '❌ UNSAFE'}")
    print(f"🔋 Pozostało quota: {safety['remaining_quota']}")
    
    # Test 3: Dry run
    result = collector.collect_data_safely(test_channels, 7, dry_run=True)
    print(f"\n🧪 Dry run: {result.get('message', 'ERROR')}") 