import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class StateManager:
    """Zarządza trwałymi danymi systemu"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Pliki z danymi
        self.channels_file = self.data_dir / "channels.json"
        self.quota_file = self.data_dir / "quota_state.json"
        self.system_state_file = self.data_dir / "system_state.json"
        
        # Inicjalizacja danych
        self.channels_data = {}
        self.quota_state = {}
        self.system_state = {}
        
        # Załaduj dane przy starcie
        self.load_all_data()
    
    def load_all_data(self):
        """Ładuje wszystkie dane z plików"""
        try:
            self.load_channels()
            self.load_quota_state()
            self.load_system_state()
            logger.info("Wszystkie dane załadowane pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych: {e}")
    
    def load_channels(self) -> Dict[str, List[Dict]]:
        """Ładuje dane kanałów z pliku"""
        try:
            if self.channels_file.exists():
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    self.channels_data = json.load(f)
                logger.info(f"Załadowano {sum(len(channels) for channels in self.channels_data.values())} kanałów")
            else:
                self.channels_data = {}
                logger.info("Utworzono nowy plik kanałów")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania kanałów: {e}")
            self.channels_data = {}
        
        return self.channels_data
    
    def save_channels(self):
        """Zapisuje dane kanałów do pliku"""
        try:
            with open(self.channels_file, 'w', encoding='utf-8') as f:
                json.dump(self.channels_data, f, ensure_ascii=False, indent=2)
            logger.info("Kanały zapisane pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania kanałów: {e}")
    
    def load_quota_state(self) -> Dict:
        """Ładuje stan quota z pliku"""
        try:
            if self.quota_file.exists():
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    self.quota_state = json.load(f)
                
                # Sprawdź czy quota nie jest przestarzałe (więcej niż 24h)
                last_reset = self.quota_state.get('last_reset')
                if last_reset:
                    last_reset_date = datetime.fromisoformat(last_reset)
                    if datetime.now() - last_reset_date > timedelta(hours=24):
                        logger.info("Quota przestarzałe - reset")
                        self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                        self.save_quota_state()
                else:
                    self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                    self.save_quota_state()
                
                logger.info(f"Załadowano stan quota: {self.quota_state.get('used', 0)}")
            else:
                self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                self.save_quota_state()
                logger.info("Utworzono nowy stan quota")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania stanu quota: {e}")
            self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
        
        return self.quota_state
    
    def save_quota_state(self):
        """Zapisuje stan quota do pliku"""
        try:
            with open(self.quota_file, 'w', encoding='utf-8') as f:
                json.dump(self.quota_state, f, ensure_ascii=False, indent=2)
            logger.debug("Stan quota zapisany pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania stanu quota: {e}")
    
    def load_system_state(self) -> Dict:
        """Ładuje stan systemu z pliku"""
        try:
            if self.system_state_file.exists():
                with open(self.system_state_file, 'r', encoding='utf-8') as f:
                    self.system_state = json.load(f)
                logger.info("Stan systemu załadowany pomyślnie")
            else:
                self.system_state = {
                    'last_startup': datetime.now().isoformat(),
                    'total_reports_generated': 0,
                    'last_report_date': None
                }
                self.save_system_state()
                logger.info("Utworzono nowy stan systemu")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania stanu systemu: {e}")
            self.system_state = {
                'last_startup': datetime.now().isoformat(),
                'total_reports_generated': 0,
                'last_report_date': None
            }
        
        return self.system_state
    
    def save_system_state(self):
        """Zapisuje stan systemu do pliku"""
        try:
            with open(self.system_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_state, f, ensure_ascii=False, indent=2)
            logger.debug("Stan systemu zapisany pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania stanu systemu: {e}")
    
    # Metody do zarządzania kanałami
    def add_channel(self, channel_data: Dict, category: str = "general"):
        """Dodaje kanał i zapisuje do pliku"""
        if category not in self.channels_data:
            self.channels_data[category] = []
        
        # Sprawdź czy kanał już istnieje
        existing_ids = [ch['id'] for ch in self.channels_data[category]]
        if channel_data['id'] not in existing_ids:
            self.channels_data[category].append(channel_data)
            self.save_channels()
            logger.info(f"Dodano kanał {channel_data['title']} do kategorii {category}")
            return True
        else:
            logger.warning(f"Kanał {channel_data['title']} już istnieje w kategorii {category}")
            return False
    
    def remove_channel(self, channel_id: str, category: str = "general"):
        """Usuwa kanał i zapisuje do pliku"""
        if category in self.channels_data:
            original_count = len(self.channels_data[category])
            self.channels_data[category] = [
                ch for ch in self.channels_data[category]
                if ch['id'] != channel_id
            ]
            
            if len(self.channels_data[category]) < original_count:
                self.save_channels()
                logger.info(f"Usunięto kanał {channel_id} z kategorii {category}")
                return True
            else:
                logger.warning(f"Kanał {channel_id} nie został znaleziony w kategorii {category}")
                return False
        return False
    
    def get_channels(self) -> Dict[str, List[Dict]]:
        """Zwraca wszystkie kanały"""
        return self.channels_data
    
    # Metody do zarządzania quota
    def get_quota_used(self) -> int:
        """Zwraca zużyte quota"""
        return self.quota_state.get('used', 0)
    
    def add_quota_used(self, amount: int):
        """Dodaje zużyte quota i zapisuje"""
        current_used = self.quota_state.get('used', 0)
        self.quota_state['used'] = current_used + amount
        self.save_quota_state()
        logger.debug(f"Dodano {amount} quota, łącznie: {self.quota_state['used']}")
    
    def reset_quota(self):
        """Resetuje quota i zapisuje"""
        self.quota_state = {
            'used': 0,
            'last_reset': datetime.now().isoformat()
        }
        self.save_quota_state()
        logger.info("Quota zostało zresetowane")
    
    def get_quota_state(self) -> Dict:
        """Zwraca pełny stan quota"""
        return self.quota_state
    
    def persist_quota(self, quota_used: int):
        """Zapisuje aktualne zużycie quota do pliku"""
        try:
            self.quota_state['used'] = quota_used
            self.quota_state['last_updated'] = datetime.now().isoformat()
            self.save_quota_state()
            logger.info(f"Zapisano quota: {quota_used}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania quota: {e}")
    
    def get_persisted_quota(self) -> int:
        """Zwraca ostatnie zapisane zużycie quota"""
        return self.quota_state.get('used', 0)
    
    # Metody do zarządzania stanem systemu
    def update_system_state(self, key: str, value):
        """Aktualizuje stan systemu i zapisuje"""
        self.system_state[key] = value
        self.save_system_state()
    
    def get_system_state(self) -> Dict:
        """Zwraca stan systemu"""
        return self.system_state
    
    # Metody do czyszczenia danych
    def clear_all_data(self):
        """Czyści wszystkie dane (dla testów)"""
        try:
            self.channels_data = {}
            self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
            self.system_state = {
                'last_startup': datetime.now().isoformat(),
                'total_reports_generated': 0,
                'last_report_date': None
            }
            
            self.save_channels()
            self.save_quota_state()
            self.save_system_state()
            
            logger.info("Wszystkie dane zostały wyczyszczone")
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia danych: {e}")
    
    def get_data_stats(self) -> Dict:
        """Zwraca statystyki danych"""
        try:
            return {
                'channels_count': sum(len(channels) for channels in self.channels_data.values()),
                'categories_count': len(self.channels_data),
                'quota_used': self.quota_state.get('used', 0),
                'quota_last_reset': self.quota_state.get('last_reset'),
                'system_startup': self.system_state.get('last_startup'),
                'reports_generated': self.system_state.get('total_reports_generated', 0),
                'data_files': {
                    'channels_file_size': self.channels_file.stat().st_size if self.channels_file.exists() else 0,
                    'quota_file_size': self.quota_file.stat().st_size if self.quota_file.exists() else 0,
                    'system_state_file_size': self.system_state_file.stat().st_size if self.system_state_file.exists() else 0
                }
            }
        except Exception as e:
            logger.error(f"Błąd podczas pobierania statystyk danych: {e}")
            return {'error': str(e)} 