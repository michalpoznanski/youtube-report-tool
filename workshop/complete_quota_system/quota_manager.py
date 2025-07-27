#!/usr/bin/env python3
"""
Quota Manager - Inteligentny system zarządzania YouTube API quota
Sprawdza quota przed operacjami, szacuje koszty i loguje zużycie
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class QuotaManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.quota_log_file = 'quota_usage.json'
        self.daily_limit = 10000
        self.load_quota_history()
        
    def load_quota_history(self):
        """Wczytuje historię zużycia quota"""
        try:
            with open(self.quota_log_file, 'r', encoding='utf-8') as f:
                self.quota_history = json.load(f)
        except FileNotFoundError:
            self.quota_history = {
                'daily_usage': {},
                'operations': [],
                'last_reset': None
            }
    
    def save_quota_history(self):
        """Zapisuje historię zużycia quota"""
        with open(self.quota_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.quota_history, f, indent=2, ensure_ascii=False)
    
    def check_quota_status(self) -> Dict:
        """Sprawdza aktualny status quota przez testowe zapytanie"""
        try:
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    'part': 'snippet',
                    'q': 'test',
                    'key': self.api_key,
                    'maxResults': 1
                },
                timeout=10
            )
            
            # LOGUJ KAŻDE ZAPYTANIE DO API
            if response.status_code == 200:
                # Udane zapytanie - zużywa 100 quota (search operation)
                self.log_operation('quota_check', {}, 100, True)
                return {
                    'status': 'available',
                    'message': 'Quota dostępne',
                    'available': self.get_estimated_available_quota()
                }
            elif response.status_code == 403 and 'quotaExceeded' in response.text:
                # Quota wyczerpane - nie zużywa dodatkowych quota
                return {
                    'status': 'exceeded',
                    'message': 'Quota wyczerpane - czekaj na reset (północ UTC)',
                    'available': 0
                }
            else:
                # Inny błąd - może zużywać quota
                self.log_operation('quota_check_error', {'status_code': response.status_code}, 100, False)
                return {
                    'status': 'error',
                    'message': f'Błąd połączenia: {response.status_code}',
                    'available': 0
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Błąd połączenia: {str(e)}',
                'available': 0
            }
    
    def get_estimated_available_quota(self) -> int:
        """Szacuje dostępne quota na podstawie dziennego zużycia"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_usage = self.quota_history['daily_usage'].get(today, 0)
        return max(0, self.daily_limit - today_usage)
    
    def estimate_operation_cost(self, operation_type: str, params: Dict) -> int:
        """Szacuje koszt operacji na podstawie typu i parametrów"""
        base_costs = {
            'channels_list': 1,
            'playlist_items': 1,
            'videos_list': 1,
            'search': 100,
            'video_details': 1
        }
        
        if operation_type == 'analyze_showbiz':
            # Szacunek dla analizy showbiz
            num_channels = params.get('num_channels', 20)
            days = params.get('days', 7)
            return num_channels * 2 + (num_channels * days * 0.5)
        
        elif operation_type == 'collect_data':
            # Szacunek dla zbierania danych
            num_channels = params.get('num_channels', 20)
            days = params.get('days', 7)
            # Koszt: 1 za playlist + 1 za szczegóły filmu + szacunkowo 2-3 filmy dziennie na kanał
            return num_channels * 2 + (num_channels * days * 2.5)
            return num_channels * 3
        
        elif operation_type == 'single_channel':
            # Pojedynczy kanał
            return 2
        
        elif operation_type == 'track_channels':
            # Szacunek dla dodawania kanałów przez !śledź
            num_videos = params.get('num_videos', 0)
            num_handles = params.get('num_handles', 0) 
            num_channels = params.get('num_channels', 0)
            
            cost = 0
            cost += num_videos * 1      # Videos API: 1 punkt za film
            cost += num_handles * 100   # Search API: 100 punktów za @handle
            cost += (num_channels - num_handles) * 1  # Channels API: 1 punkt za /c/
            
            return cost
        
        else:
            return base_costs.get(operation_type, 10)
    
    def can_perform_operation(self, operation_type: str, params: Dict) -> Tuple[bool, Dict]:
        """Sprawdza czy można wykonać operację bez przekroczenia quota"""
        # Sprawdź status quota
        quota_status = self.check_quota_status()
        
        if quota_status['status'] == 'exceeded':
            return False, {
                'can_perform': False,
                'reason': 'Quota wyczerpane',
                'message': 'Poczekaj do północy UTC na reset quota',
                'quota_status': quota_status
            }
        
        # Szacuj koszt operacji
        estimated_cost = self.estimate_operation_cost(operation_type, params)
        available_quota = quota_status['available']
        
        # Dodaj margines bezpieczeństwa (20%)
        safe_quota = available_quota * 0.8
        
        if estimated_cost > safe_quota:
            return False, {
                'can_perform': False,
                'reason': 'Niewystarczające quota',
                'message': f'Potrzebne: {estimated_cost}, dostępne: {available_quota}',
                'estimated_cost': estimated_cost,
                'available_quota': available_quota,
                'quota_status': quota_status
            }
        
        return True, {
            'can_perform': True,
            'estimated_cost': estimated_cost,
            'available_quota': available_quota,
            'quota_status': quota_status
        }
    
    def log_operation(self, operation_type: str, params: Dict, actual_cost: int, success: bool):
        """Loguje wykonaną operację i zużyte quota"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Aktualizuj dzienne zużycie
        if today not in self.quota_history['daily_usage']:
            self.quota_history['daily_usage'][today] = 0
        self.quota_history['daily_usage'][today] += actual_cost
        
        # Dodaj szczegóły operacji
        operation_log = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'params': params,
            'estimated_cost': self.estimate_operation_cost(operation_type, params),
            'actual_cost': actual_cost,
            'success': success,
            'daily_total': self.quota_history['daily_usage'][today]
        }
        
        self.quota_history['operations'].append(operation_log)
        
        # Zachowaj tylko ostatnie 100 operacji
        if len(self.quota_history['operations']) > 100:
            self.quota_history['operations'] = self.quota_history['operations'][-100:]
        
        self.save_quota_history()
    
    def get_quota_summary(self) -> Dict:
        """Zwraca podsumowanie zużycia quota z weryfikacją API"""
        # AUTOMATYCZNY RESET QUOTA - sprawdź czy minęła północ UTC
        self._check_and_reset_quota()
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_usage = self.quota_history['daily_usage'].get(today, 0)
        
        # Sprawdź wczorajsze zużycie dla kontekstu
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_usage = self.quota_history['daily_usage'].get(yesterday, 0)
        
        # SPRAWDŹ RZECZYWISTY STATUS API
        quota_status = self.check_quota_status()
        
        # Jeśli API zwraca quota exceeded, ustaw zużycie na maksimum
        if quota_status.get('status') == 'exceeded':
            if today_usage == 0:
                # API mówi że quota wyczerpane ale lokalnie 0 - używane poza botem
                today_usage = self.daily_limit
                quota_warning = "⚠️ QUOTA WYCZERPANE - użyte poza botem lub reset nie nastąpił"
            else:
                # Zgodne z lokalnymi danymi
                quota_warning = "⚠️ QUOTA WYCZERPANE (weryfikacja API)"
        elif quota_status.get('status') == 'available' and today_usage == 0:
            # API dostępne ale lokalne zużycie = 0 - prawdopodobnie nowy dzień
            quota_warning = "✅ QUOTA DOSTĘPNE (nowy dzień)"
        else:
            quota_warning = None
        
        # Oblicz średnie dzienne zużycie z ostatnich 7 dni
        last_7_days = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            usage = self.quota_history['daily_usage'].get(date, 0)
            last_7_days.append(usage)
        
        avg_daily_usage = sum(last_7_days) / len(last_7_days)
        
        return {
            'today_usage': today_usage,
            'yesterday_usage': yesterday_usage,
            'today_remaining': max(0, self.daily_limit - today_usage),
            'daily_limit': self.daily_limit,
            'usage_percentage': (today_usage / self.daily_limit) * 100,
            'avg_daily_usage': avg_daily_usage,
            'last_7_days': last_7_days,
            'quota_status': quota_status,
            'api_verified': True,
            'warning': quota_warning
        }
    
    def get_operation_history(self, limit: int = 10) -> List[Dict]:
        """Zwraca historię ostatnich operacji"""
        return self.quota_history['operations'][-limit:]
    
    def _check_and_reset_quota(self):
        """Automatycznie resetuje quota jeśli minęła północ UTC"""
        today = datetime.now().strftime('%Y-%m-%d')
        last_reset = self.quota_history.get('last_reset')
        
        # Jeśli nie było jeszcze resetu lub ostatni reset był wczoraj lub wcześniej
        if not last_reset or last_reset[:10] < today:
            # Sprawdź czy quota rzeczywiście powinny być zresetowane
            # (czy są jakieś dane z wcześniejszych dni)
            dates_to_check = list(self.quota_history['daily_usage'].keys())
            if dates_to_check and max(dates_to_check) < today:
                # Ostatnie zużycie było wcześniej niż dzisiaj - resetuj quota
                self.quota_history['last_reset'] = datetime.now().isoformat()
                self.save_quota_history()
                print(f"🔄 Auto-reset quota na dzień {today}")
    
    def reset_daily_usage(self):
        """Resetuje dzienne zużycie (do użycia o północy UTC)"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.quota_history['daily_usage']:
            del self.quota_history['daily_usage'][today]
        self.quota_history['last_reset'] = datetime.now().isoformat()
        self.save_quota_history()

# Przykład użycia
if __name__ == "__main__":
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Brak YOUTUBE_API_KEY")
        exit(1)
    
    quota_manager = QuotaManager(api_key)
    
    # Test sprawdzenia quota
    print("🔍 Sprawdzam status quota...")
    status = quota_manager.check_quota_status()
    print(f"Status: {status['status']}")
    print(f"Wiadomość: {status['message']}")
    
    # Test szacowania kosztów
    print("\n💰 Szacowanie kosztów operacji:")
    operations = [
        ('analyze_showbiz', {'num_channels': 20, 'days': 7}),
        ('collect_data', {'num_channels': 20}),
        ('single_channel', {})
    ]
    
    for op_type, params in operations:
        cost = quota_manager.estimate_operation_cost(op_type, params)
        print(f"  {op_type}: {cost} quota")
    
    # Test sprawdzenia możliwości wykonania
    print("\n✅ Sprawdzam możliwość wykonania analizy showbiz...")
    can_perform, details = quota_manager.can_perform_operation('analyze_showbiz', {'num_channels': 20, 'days': 7})
    print(f"Można wykonać: {can_perform}")
    print(f"Szczegóły: {details}")
    
    # Podsumowanie quota
    print("\n📊 Podsumowanie quota:")
    summary = quota_manager.get_quota_summary()
    print(f"Dzisiejsze zużycie: {summary['today_usage']} / {summary['daily_limit']}")
    print(f"Pozostało: {summary['today_remaining']}")
    print(f"Procent zużycia: {summary['usage_percentage']:.1f}%") 