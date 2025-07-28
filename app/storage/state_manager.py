import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class StateManager:
    """Zarządza trwałymi danymi systemu"""
    
    def __init__(self, data_dir: str = None):
        print(f"[INIT] StateManager initialization started")
        
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie domyślny katalog
        if data_dir is None:
            import os
            railway_volume = os.getenv("RAILWAY_VOLUME_PATH")
            if railway_volume:
                data_dir = os.path.join(railway_volume, "data")
                print(f"[INIT] Using Railway Volume Path: {data_dir}")
            else:
                data_dir = "data"
                print(f"[INIT] Using default directory: {data_dir}")
        
        self.data_dir = Path(data_dir)
        print(f"[INIT] Data directory set to: {self.data_dir.absolute()}")
        
        # Sprawdź i utwórz katalog jeśli nie istnieje
        self._ensure_data_directory()
        
        # Pliki z danymi
        self.channels_file = self.data_dir / "channels.json"
        self.quota_file = self.data_dir / "quota_state.json"
        self.system_state_file = self.data_dir / "system_state.json"
        
        print(f"[INIT] File paths:")
        print(f"[INIT]   channels: {self.channels_file.absolute()}")
        print(f"[INIT]   quota: {self.quota_file.absolute()}")
        print(f"[INIT]   system: {self.system_state_file.absolute()}")
        
        # Inicjalizacja danych
        self.channels_data = {}
        self.quota_state = {}
        self.system_state = {}
        
        # Załaduj dane przy starcie
        print(f"[INIT] Loading all data...")
        self.load_all_data()
        print(f"[INIT] StateManager initialization completed")
    
    def _ensure_data_directory(self):
        """Sprawdza i tworzy katalog danych z odpowiednimi uprawnieniami"""
        try:
            if not self.data_dir.exists():
                print(f"📁 Tworzenie katalogu danych: {self.data_dir.absolute()}")
                self.data_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ Katalog utworzony: {self.data_dir.absolute()}")
            else:
                print(f"📁 Katalog danych istnieje: {self.data_dir.absolute()}")
            
            # Sprawdź uprawnienia do zapisu
            test_file = self.data_dir / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print(f"✅ Uprawnienia do zapisu OK: {self.data_dir.absolute()}")
            except Exception as e:
                print(f"❌ Brak uprawnień do zapisu: {self.data_dir.absolute()} - {e}")
                # Spróbuj alternatywny katalog
                alt_dir = Path("/tmp/data")
                print(f"🔄 Próba użycia alternatywnego katalogu: {alt_dir}")
                alt_dir.mkdir(parents=True, exist_ok=True)
                self.data_dir = alt_dir
                
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia katalogu danych: {e}")
            # Fallback do katalogu roboczego
            self.data_dir = Path("data")
            self.data_dir.mkdir(exist_ok=True)
    
    def load_all_data(self):
        """Ładuje wszystkie dane z plików"""
        try:
            print("🔄 Ładowanie danych z plików JSON...")
            print(f"[LOAD_ALL] Starting data load from: {self.data_dir.absolute()}")
            logger.info("🔄 Ładowanie danych z plików JSON...")
            
            self.load_channels()
            self.load_quota_state()
            self.load_system_state()
            
            # Wyświetl podsumowanie wczytanych danych
            channels_count = sum(len(channels) for channels in self.channels_data.values())
            quota_used = self.quota_state.get('used', 0)
            last_reset = self.quota_state.get('last_reset', 'Nieznana')
            
            print(f"[LOAD_ALL] Load summary:")
            print(f"[LOAD_ALL]   channels_count: {channels_count}")
            print(f"[LOAD_ALL]   quota_used: {quota_used}")
            print(f"[LOAD_ALL]   last_reset: {last_reset}")
            
            print(f"✅ Dane wczytane pomyślnie:")
            print(f"   📺 Kanały: {channels_count}")
            print(f"   📊 Quota użyte: {quota_used}")
            print(f"   🕐 Ostatni reset: {last_reset}")
            print(f"   📁 Katalog danych: {self.data_dir.absolute()}")
            
            logger.info(f"✅ Dane wczytane pomyślnie - Kanały: {channels_count}, Quota: {quota_used}")
        except Exception as e:
            print(f"[LOAD_ALL] Error loading all data: {e}")
            print(f"❌ Błąd podczas ładowania danych: {e}")
            logger.error(f"Błąd podczas ładowania danych: {e}")
    
    def load_channels(self) -> Dict[str, List[Dict]]:
        """Ładuje dane kanałów z pliku"""
        try:
            print(f"[LOAD] channels.json exists: {self.channels_file.exists()}")
            print(f"[LOAD] channels.json path: {self.channels_file.absolute()}")
            
            if self.channels_file.exists():
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    self.channels_data = json.load(f)
                
                print(f"[LOAD] channels content: {self.channels_data}")
                
                channels_count = sum(len(channels) for channels in self.channels_data.values())
                categories = list(self.channels_data.keys())
                
                print(f"📺 Załadowano {channels_count} kanałów z kategorii: {categories}")
                logger.info(f"Załadowano {channels_count} kanałów z kategorii: {categories}")
                
                # Wyświetl szczegóły kanałów
                for category, channels in self.channels_data.items():
                    print(f"   📂 {category}: {len(channels)} kanałów")
                    for channel in channels:
                        print(f"      - {channel.get('title', 'Unknown')} ({channel.get('id', 'No ID')})")
            else:
                self.channels_data = {}
                print("[LOAD] channels.json does not exist - creating empty data")
                print("📁 Utworzono nowy plik kanałów (brak istniejących danych)")
                logger.info("Utworzono nowy plik kanałów")
        except Exception as e:
            print(f"[LOAD] Error loading channels: {e}")
            print(f"❌ Błąd podczas ładowania kanałów: {e}")
            logger.error(f"Błąd podczas ładowania kanałów: {e}")
            self.channels_data = {}
        
        return self.channels_data
    
    def save_channels(self):
        """Zapisuje dane kanałów do pliku"""
        try:
            print(f"[SAVE] Saving channels to: {self.channels_file.absolute()}")
            print(f"[SAVE] channels data: {self.channels_data}")
            
            with open(self.channels_file, 'w', encoding='utf-8') as f:
                json.dump(self.channels_data, f, ensure_ascii=False, indent=2)
            
            print(f"[SAVE] channels saved successfully")
            logger.info("Kanały zapisane pomyślnie")
        except Exception as e:
            print(f"[SAVE] Error saving channels: {e}")
            logger.error(f"Błąd podczas zapisywania kanałów: {e}")
    
    def load_quota_state(self) -> Dict:
        """Ładuje stan quota z pliku"""
        try:
            print(f"[LOAD] quota_state.json exists: {self.quota_file.exists()}")
            print(f"[LOAD] quota_state.json path: {self.quota_file.absolute()}")
            
            if self.quota_file.exists():
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    self.quota_state = json.load(f)
                
                print(f"[LOAD] quota content: {self.quota_state}")
                
                # Sprawdź czy quota nie jest przestarzałe (więcej niż 24h)
                last_reset = self.quota_state.get('last_reset')
                if last_reset:
                    last_reset_date = datetime.fromisoformat(last_reset)
                    if datetime.now() - last_reset_date > timedelta(hours=24):
                        print("🔄 Quota przestarzałe - reset")
                        logger.info("Quota przestarzałe - reset")
                        self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                        self.save_quota_state()
                else:
                    self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                    self.save_quota_state()
                
                quota_used = self.quota_state.get('used', 0)
                last_reset = self.quota_state.get('last_reset', 'Nieznana')
                print(f"📊 Załadowano stan quota: {quota_used} użyte, ostatni reset: {last_reset}")
                logger.info(f"Załadowano stan quota: {quota_used}")
            else:
                print("[LOAD] quota_state.json does not exist - creating new")
                self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
                self.save_quota_state()
                print("📁 Utworzono nowy stan quota (brak istniejących danych)")
                logger.info("Utworzono nowy stan quota")
        except Exception as e:
            print(f"[LOAD] Error loading quota: {e}")
            print(f"❌ Błąd podczas ładowania stanu quota: {e}")
            logger.error(f"Błąd podczas ładowania stanu quota: {e}")
            self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
        
        return self.quota_state
    
    def save_quota_state(self):
        """Zapisuje stan quota do pliku"""
        try:
            print(f"[SAVE] Saving quota to: {self.quota_file.absolute()}")
            print(f"[SAVE] quota data: {self.quota_state}")
            
            with open(self.quota_file, 'w', encoding='utf-8') as f:
                json.dump(self.quota_state, f, ensure_ascii=False, indent=2)
            
            print(f"[SAVE] quota saved successfully")
            logger.debug("Stan quota zapisany pomyślnie")
        except Exception as e:
            print(f"[SAVE] Error saving quota: {e}")
            logger.error(f"Błąd podczas zapisywania stanu quota: {e}")
    
    def load_system_state(self) -> Dict:
        """Ładuje stan systemu z pliku"""
        try:
            print(f"[LOAD] system_state.json exists: {self.system_state_file.exists()}")
            print(f"[LOAD] system_state.json path: {self.system_state_file.absolute()}")
            
            if self.system_state_file.exists():
                with open(self.system_state_file, 'r', encoding='utf-8') as f:
                    self.system_state = json.load(f)
                
                print(f"[LOAD] system_state content: {self.system_state}")
                logger.info("Stan systemu załadowany pomyślnie")
            else:
                print("[LOAD] system_state.json does not exist - creating new")
                self.system_state = {
                    'last_startup': datetime.now().isoformat(),
                    'total_reports_generated': 0,
                    'last_report_date': None
                }
                self.save_system_state()
                logger.info("Utworzono nowy stan systemu")
        except Exception as e:
            print(f"[LOAD] Error loading system_state: {e}")
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
            print(f"[SAVE] Saving system_state to: {self.system_state_file.absolute()}")
            print(f"[SAVE] system_state data: {self.system_state}")
            
            with open(self.system_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_state, f, ensure_ascii=False, indent=2)
            
            print(f"[SAVE] system_state saved successfully")
            logger.debug("Stan systemu zapisany pomyślnie")
        except Exception as e:
            print(f"[SAVE] Error saving system_state: {e}")
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