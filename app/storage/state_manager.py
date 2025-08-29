try:
    import json
    import logging
    import os
    from pathlib import Path
    from typing import Dict, List, Optional, Any
    from datetime import datetime, timedelta
    import re
    from ..config import settings
    
    print("✅ Wszystkie importy w state_manager udane")
except ImportError as e:
    print(f"❌ Błąd importu w state_manager: {e}")
    import traceback
    traceback.print_exc()
    raise

logger = logging.getLogger(__name__)


class StateManager:
    """Zarządza trwałymi danymi systemu z obsługą Railway Volume Path"""
    
    def __init__(self, data_dir: str = None):
        print(f"[INIT] StateManager initialization started")
        
        # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie domyślny katalog /mnt/volume
        if data_dir is None:
            railway_volume = os.getenv("RAILWAY_VOLUME_PATH")
            if railway_volume:
                data_dir = os.path.join(railway_volume, "data")
                print(f"[INIT] Using Railway Volume Path: {data_dir}")
                logger.info(f"Using Railway Volume Path: {data_dir}")
            else:
                data_dir = "/mnt/volume/data"
                print(f"[INIT] Using default persistent directory: {data_dir}")
                logger.info(f"Using default persistent directory: {data_dir}")
        
        self.data_dir = Path(data_dir)
        print(f"[INIT] Data directory set to: {self.data_dir.absolute()}")
        logger.info(f"Data directory set to: {self.data_dir.absolute()}")
        
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
        logger.info(f"File paths - channels: {self.channels_file.absolute()}, quota: {self.quota_file.absolute()}, system: {self.system_state_file.absolute()}")
        
        # Inicjalizacja danych
        self.channels_data = {}
        self.quota_state = {}
        self.system_state = {}
        
        # Mapy do śledzenia kanałów (dla walidacji duplikatów)
        self.channel_id_map = {}
        self.channel_url_map = {}
        
        # Załaduj dane przy starcie
        print(f"[INIT] Loading all data...")
        self.load_all_data()
        print(f"[INIT] StateManager initialization completed")
        logger.info("StateManager initialization completed")
    
    def _ensure_data_directory(self):
        """Sprawdza i tworzy katalog danych z odpowiednimi uprawnieniami"""
        try:
            print(f"[DIR] Checking data directory: {self.data_dir.absolute()}")
            logger.info(f"Checking data directory: {self.data_dir.absolute()}")
            
            if not self.data_dir.exists():
                print(f"[DIR] Creating data directory: {self.data_dir.absolute()}")
                logger.info(f"Creating data directory: {self.data_dir.absolute()}")
                self.data_dir.mkdir(parents=True, exist_ok=True)
                print(f"[DIR] Data directory created: {self.data_dir.absolute()}")
                logger.info(f"Data directory created: {self.data_dir.absolute()}")
            else:
                print(f"[DIR] Data directory exists: {self.data_dir.absolute()}")
                logger.info(f"Data directory exists: {self.data_dir.absolute()}")
            
            # Sprawdź uprawnienia do zapisu
            test_file = self.data_dir / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print(f"[DIR] Write permissions OK: {self.data_dir.absolute()}")
                logger.info(f"Write permissions OK: {self.data_dir.absolute()}")
            except Exception as e:
                print(f"[DIR] Write permission error: {self.data_dir.absolute()} - {e}")
                logger.error(f"Write permission error: {self.data_dir.absolute()} - {e}")
                # Spróbuj alternatywny katalog
                alt_dir = Path("/tmp/data")
                print(f"[DIR] Trying alternative directory: {alt_dir}")
                logger.warning(f"Trying alternative directory: {alt_dir}")
                alt_dir.mkdir(parents=True, exist_ok=True)
                self.data_dir = alt_dir
                
        except Exception as e:
            print(f"[DIR] Error creating data directory: {e}")
            logger.error(f"Error creating data directory: {e}")
            # Fallback do katalogu roboczego
            self.data_dir = Path("data")
            self.data_dir.mkdir(exist_ok=True)
            print(f"[DIR] Fallback to working directory: {self.data_dir.absolute()}")
            logger.warning(f"Fallback to working directory: {self.data_dir.absolute()}")
    
    def _safe_write_file(self, file_path: Path, data: dict):
        """Bezpieczny zapis pliku z flush() i fsync()"""
        try:
            print(f"[SAVE] Safe writing to: {file_path.absolute()}")
            logger.info(f"Safe writing to: {file_path.absolute()}")
            
            # Zapisz do pliku tymczasowego
            temp_file = file_path.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()  # Wymuś zapis do bufora
                os.fsync(f.fileno())  # Wymuś zapis na dysk
            
            # Przenieś plik tymczasowy do docelowego
            temp_file.replace(file_path)
            
            print(f"[SAVE] File written successfully: {file_path.absolute()}")
            logger.info(f"File written successfully: {file_path.absolute()}")
            
        except Exception as e:
            print(f"[SAVE] Error writing file {file_path}: {e}")
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    def _safe_read_file(self, file_path: Path) -> dict:
        """Bezpieczny odczyt pliku"""
        try:
            print(f"[LOAD] Safe reading from: {file_path.absolute()}")
            logger.info(f"Safe reading from: {file_path.absolute()}")
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"[LOAD] File read successfully: {file_path.absolute()}")
                logger.info(f"File read successfully: {file_path.absolute()}")
                return data
            else:
                print(f"[LOAD] File does not exist: {file_path.absolute()}")
                logger.info(f"File does not exist: {file_path.absolute()}")
                return {}
                
        except Exception as e:
            print(f"[LOAD] Error reading file {file_path}: {e}")
            logger.error(f"Error reading file {file_path}: {e}")
            return {}
    
    def load_all_data(self):
        """Ładuje wszystkie dane z plików"""
        try:
            print("🔄 Ładowanie danych z plików JSON...")
            print(f"[LOAD_ALL] Starting data load from: {self.data_dir.absolute()}")
            logger.info("🔄 Ładowanie danych z plików JSON...")
            logger.info(f"Starting data load from: {self.data_dir.absolute()}")
            
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
            print(f"[LOAD_ALL]   data_directory: {self.data_dir.absolute()}")
            
            print(f"✅ Dane wczytane pomyślnie:")
            print(f"   📺 Kanały: {channels_count}")
            print(f"   📊 Quota użyte: {quota_used}")
            print(f"   🕐 Ostatni reset: {last_reset}")
            print(f"   📁 Katalog danych: {self.data_dir.absolute()}")
            
            logger.info(f"✅ Dane wczytane pomyślnie - Kanały: {channels_count}, Quota: {quota_used}")
            logger.info(f"Data directory: {self.data_dir.absolute()}")
        except Exception as e:
            print(f"[LOAD_ALL] Error loading all data: {e}")
            print(f"❌ Błąd podczas ładowania danych: {e}")
            logger.error(f"Błąd podczas ładowania danych: {e}")
    
    def load_channels(self) -> Dict[str, List[Dict]]:
        """Ładuje dane kanałów z pliku z walidacją i czyszczeniem"""
        try:
            print(f"[LOAD] channels.json exists: {self.channels_file.exists()}")
            print(f"[LOAD] channels.json path: {self.channels_file.absolute()}")
            
            # Wczytaj surowe dane
            raw_channels_data = self._safe_read_file(self.channels_file)
            
            if raw_channels_data:
                print(f"[LOAD] Raw channels data loaded: {len(raw_channels_data)} categories")
                logger.info(f"Raw channels data loaded: {len(raw_channels_data)} categories")
                
                # Waliduj i wyczyść dane
                cleaned_channels_data = {}
                corrupted_entries = []
                duplicate_entries = []
                
                # Mapy do śledzenia duplikatów
                channel_id_map = {}
                channel_url_map = {}
                
                for category, channels in raw_channels_data.items():
                    print(f"[VALIDATE] Processing category: {category} ({len(channels)} channels)")
                    logger.info(f"Processing category: {category} ({len(channels)} channels)")
                    
                    valid_channels = []
                    
                    for i, channel in enumerate(channels):
                        channel_id = channel.get('id', '')
                        channel_name = channel.get('title', '')
                        channel_url = channel.get('url', '')
                        channel_category = category
                        
                        # Sprawdź czy kanał ma wszystkie wymagane pola
                        is_valid = True
                        validation_errors = []
                        
                        # 1. Sprawdź channel_id (zaczyna się od "UC")
                        if not channel_id or not channel_id.startswith('UC'):
                            validation_errors.append(f"Invalid channel_id: {channel_id}")
                            is_valid = False
                        
                        # 2. Sprawdź channel_name
                        if not channel_name:
                            validation_errors.append("Missing channel_name")
                            is_valid = False
                        
                        # 3. Sprawdź url
                        if not channel_url:
                            validation_errors.append("Missing url")
                            is_valid = False
                        elif not self._validate_youtube_url(channel_url):
                            validation_errors.append(f"Invalid YouTube URL format: {channel_url}")
                            is_valid = False
                        
                        # 4. Sprawdź category
                        if not channel_category:
                            validation_errors.append("Missing category")
                            is_valid = False
                        
                        # Sprawdź duplikaty
                        if is_valid:
                            # Sprawdź duplikat channel_id
                            if channel_id in channel_id_map:
                                duplicate_info = channel_id_map[channel_id]
                                validation_errors.append(f"Duplicate channel_id: {channel_id} (already exists in {duplicate_info['category']}: {duplicate_info['name']})")
                                is_valid = False
                                duplicate_entries.append({
                                    'channel_id': channel_id,
                                    'channel_name': channel_name,
                                    'category': category,
                                    'index': i,
                                    'conflict_with': duplicate_info
                                })
                            
                            # Sprawdź duplikat url
                            elif channel_url in channel_url_map:
                                duplicate_info = channel_url_map[channel_url]
                                validation_errors.append(f"Duplicate url: {channel_url} (already exists in {duplicate_info['category']}: {duplicate_info['name']})")
                                is_valid = False
                                duplicate_entries.append({
                                    'channel_id': channel_id,
                                    'channel_name': channel_name,
                                    'category': category,
                                    'index': i,
                                    'conflict_with': duplicate_info
                                })
                        
                        # Jeśli kanał jest niepoprawny, zaloguj i pomiń
                        if not is_valid:
                            print(f"[CORRUPTED] Invalid channel in {category}[{i}]: {channel_name} ({channel_id})")
                            print(f"[CORRUPTED] Errors: {validation_errors}")
                            logger.warning(f"[CORRUPTED] Invalid channel in {category}[{i}]: {channel_name} ({channel_id}) - Errors: {validation_errors}")
                            
                            corrupted_entries.append({
                                'channel_id': channel_id,
                                'channel_name': channel_name,
                                'category': category,
                                'index': i,
                                'errors': validation_errors,
                                'original_data': channel
                            })
                            continue
                        
                        # Kanał jest poprawny - dodaj do map i listy
                        channel_id_map[channel_id] = {
                            'name': channel_name,
                            'category': category,
                            'url': channel_url
                        }
                        channel_url_map[channel_url] = {
                            'name': channel_name,
                            'category': category,
                            'id': channel_id
                        }
                        
                        valid_channels.append(channel)
                        print(f"[VALID] Valid channel: {channel_name} ({channel_id}) in {category}")
                    
                    # Dodaj kategorię (nawet jeśli pusta)
                    cleaned_channels_data[category] = valid_channels
                    if valid_channels:
                        print(f"[VALIDATE] Category {category}: {len(valid_channels)} valid channels (removed {len(channels) - len(valid_channels)} invalid)")
                    else:
                        print(f"[VALIDATE] Category {category}: no valid channels, keeping empty category")
                
                # Zaktualizuj dane kanałów
                self.channels_data = cleaned_channels_data
                
                # Zaktualizuj mapy
                self.channel_id_map = channel_id_map
                self.channel_url_map = channel_url_map
                
                # Podsumowanie walidacji
                total_original = sum(len(channels) for channels in raw_channels_data.values())
                total_valid = sum(len(channels) for channels in cleaned_channels_data.values())
                total_corrupted = len(corrupted_entries)
                total_duplicates = len(duplicate_entries)
                
                print(f"[VALIDATE] Validation summary:")
                print(f"[VALIDATE]   Original channels: {total_original}")
                print(f"[VALIDATE]   Valid channels: {total_valid}")
                print(f"[VALIDATE]   Corrupted entries: {total_corrupted}")
                print(f"[VALIDATE]   Duplicate entries: {total_duplicates}")
                print(f"[VALIDATE]   Categories: {list(cleaned_channels_data.keys())}")
                
                logger.info(f"Validation summary - Original: {total_original}, Valid: {total_valid}, Corrupted: {total_corrupted}, Duplicates: {total_duplicates}")
                
                # Jeśli były zmiany, zapisz wyczyszczone dane
                if total_original != total_valid:
                    print(f"[VALIDATE] Data was cleaned, saving updated channels.json")
                    logger.info(f"Data was cleaned, saving updated channels.json")
                    self.save_channels()
                
                # Wyświetl szczegóły kanałów
                channels_count = sum(len(channels) for channels in self.channels_data.values())
                categories = list(self.channels_data.keys())
                
                print(f"📺 Załadowano {channels_count} kanałów z kategorii: {categories}")
                logger.info(f"Załadowano {channels_count} kanałów z kategorii: {categories}")
                
                # Wyświetl szczegóły kanałów
                for category, channels in self.channels_data.items():
                    print(f"   📂 {category}: {len(channels)} kanałów")
                    for channel in channels:
                        print(f"      - {channel.get('title', 'Unknown')} ({channel.get('id', 'No ID')})")
                
                # Wyświetl szczegóły błędów jeśli były
                if corrupted_entries:
                    print(f"[CORRUPTED] Corrupted entries details:")
                    for entry in corrupted_entries:
                        print(f"   - {entry['category']}[{entry['index']}]: {entry['channel_name']} ({entry['channel_id']})")
                        print(f"     Errors: {entry['errors']}")
                
                if duplicate_entries:
                    print(f"[DUPLICATE] Duplicate entries details:")
                    for entry in duplicate_entries:
                        print(f"   - {entry['category']}[{entry['index']}]: {entry['channel_name']} ({entry['channel_id']})")
                        print(f"     Conflicts with: {entry['conflict_with']['category']}: {entry['conflict_with']['name']}")
                
            else:
                print("[LOAD] channels.json does not exist - creating empty data")
                print("📁 Utworzono nowy plik kanałów (brak istniejących danych)")
                logger.info("Utworzono nowy plik kanałów")
                self.channels_data = {}
                self.channel_id_map = {}
                self.channel_url_map = {}
                
        except Exception as e:
            print(f"[LOAD] Error loading channels: {e}")
            print(f"❌ Błąd podczas ładowania kanałów: {e}")
            logger.error(f"Błąd podczas ładowania kanałów: {e}")
            self.channels_data = {}
            self.channel_id_map = {}
            self.channel_url_map = {}
        
        return self.channels_data
    
    def save_channels(self):
        """Zapisuje dane kanałów do pliku"""
        try:
            print(f"[SAVE] Saving channels to: {self.channels_file.absolute()}")
            print(f"[SAVE] channels data: {self.channels_data}")
            
            self._safe_write_file(self.channels_file, self.channels_data)
            
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
            
            self.quota_state = self._safe_read_file(self.quota_file)
            
            if self.quota_state:
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
            
            self._safe_write_file(self.quota_file, self.quota_state)
            
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
            
            self.system_state = self._safe_read_file(self.system_state_file)
            
            if self.system_state:
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
            
            self._safe_write_file(self.system_state_file, self.system_state)
            
            print(f"[SAVE] system_state saved successfully")
            logger.debug("Stan systemu zapisany pomyślnie")
        except Exception as e:
            print(f"[SAVE] Error saving system_state: {e}")
            logger.error(f"Błąd podczas zapisywania stanu systemu: {e}")
    
    def add_channel(self, channel_data: Dict, category: str = "general"):
        """Dodaje kanał do kategorii z walidacją duplikatów"""
        try:
            channel_id = channel_data.get('id', '')
            channel_name = channel_data.get('title', '')
            channel_url = channel_data.get('url', '')
            
            print(f"[ADD] Adding channel: {channel_name} ({channel_id}) to category: {category}")
            logger.info(f"Adding channel: {channel_name} ({channel_id}) to category: {category}")
            
            # Sprawdź czy kanał ma wszystkie wymagane pola
            if not channel_id or not channel_id.startswith('UC'):
                error_msg = f"Invalid channel_id: {channel_id}"
                print(f"[ADD] Error: {error_msg}")
                logger.error(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            if not channel_name:
                error_msg = "Missing channel_name"
                print(f"[ADD] Error: {error_msg}")
                logger.error(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            if not channel_url:
                error_msg = "Missing channel_url"
                print(f"[ADD] Error: {error_msg}")
                logger.error(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            if not self._validate_youtube_url(channel_url):
                error_msg = f"Invalid YouTube URL format: {channel_url}"
                print(f"[ADD] Error: {error_msg}")
                logger.error(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            # Sprawdź duplikaty
            if channel_id in self.channel_id_map:
                existing = self.channel_id_map[channel_id]
                error_msg = f"Channel with ID {channel_id} already exists in category {existing['category']}: {existing['name']}"
                print(f"[ADD] Error: {error_msg}")
                logger.warning(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            if channel_url in self.channel_url_map:
                existing = self.channel_url_map[channel_url]
                error_msg = f"Channel with URL {channel_url} already exists in category {existing['category']}: {existing['name']}"
                print(f"[ADD] Error: {error_msg}")
                logger.warning(f"[ADD] Error: {error_msg}")
                raise ValueError(error_msg)
            
            # Inicjalizuj kategorię jeśli nie istnieje
            if category not in self.channels_data:
                self.channels_data[category] = []
                print(f"[ADD] Created new category: {category}")
            
            # Dodaj kanał do danych
            self.channels_data[category].append(channel_data)
            
            # Dodaj do map
            self.channel_id_map[channel_id] = {
                'name': channel_name,
                'category': category,
                'url': channel_url
            }
            self.channel_url_map[channel_url] = {
                'name': channel_name,
                'category': category,
                'id': channel_id
            }
            
            # Zapisz zmiany
            self.save_channels()
            
            print(f"[ADD] Successfully added channel: {channel_name} ({channel_id}) to category: {category}")
            logger.info(f"Successfully added channel: {channel_name} ({channel_id}) to category: {category}")
            
        except Exception as e:
            print(f"[ADD] Error adding channel: {e}")
            logger.error(f"Error adding channel: {e}")
            raise
    
    def remove_channel(self, channel_id: str, category: str = "general"):
        """Usuwa kanał z kategorii i aktualizuje mapy"""
        try:
            print(f"[REMOVE] Removing channel: {channel_id} from category: {category}")
            logger.info(f"Removing channel: {channel_id} from category: {category}")
            
            if category in self.channels_data:
                # Znajdź kanał do usunięcia
                channel_to_remove = None
                for channel in self.channels_data[category]:
                    if channel.get('id') == channel_id:
                        channel_to_remove = channel
                        break
                
                if channel_to_remove:
                    # Usuń z danych
                    self.channels_data[category] = [
                        c for c in self.channels_data[category] if c.get('id') != channel_id
                    ]
                    
                    # Usuń z map
                    if channel_id in self.channel_id_map:
                        removed_info = self.channel_id_map.pop(channel_id)
                        print(f"[REMOVE] Removed from channel_id_map: {channel_id}")
                    
                    channel_url = channel_to_remove.get('url', '')
                    if channel_url in self.channel_url_map:
                        self.channel_url_map.pop(channel_url)
                        print(f"[REMOVE] Removed from channel_url_map: {channel_url}")
                    
                    # Usuń pustą kategorię
                    if not self.channels_data[category]:
                        del self.channels_data[category]
                        print(f"[REMOVE] Removed empty category: {category}")
                    
                    # Zapisz zmiany
                    self.save_channels()
                    
                    print(f"[REMOVE] Successfully removed channel: {channel_id} from category: {category}")
                    logger.info(f"Successfully removed channel: {channel_id} from category: {category}")
                else:
                    error_msg = f"Channel {channel_id} not found in category {category}"
                    print(f"[REMOVE] Error: {error_msg}")
                    logger.warning(f"[REMOVE] Error: {error_msg}")
                    raise ValueError(error_msg)
            else:
                error_msg = f"Category {category} not found"
                print(f"[REMOVE] Error: {error_msg}")
                logger.warning(f"[REMOVE] Error: {error_msg}")
                raise ValueError(error_msg)
                
        except Exception as e:
            print(f"[REMOVE] Error removing channel: {e}")
            logger.error(f"Error removing channel: {e}")
            raise
    
    def get_channels(self) -> Dict[str, List[Dict]]:
        """Zwraca wszystkie kanały z dodanym polem category"""
        # Dodaj pole category do każdego kanału
        channels_with_category = {}
        
        for category, channels in self.channels_data.items():
            channels_with_category[category] = []
            for channel in channels:
                # Skopiuj kanał i dodaj pole category
                channel_with_category = channel.copy()
                channel_with_category['category'] = category
                channels_with_category[category].append(channel_with_category)
        
        return channels_with_category
    
    def get_quota_used(self) -> int:
        """Zwraca użyte quota"""
        return self.quota_state.get('used', 0)
    
    def add_quota_used(self, amount: int):
        """Dodaje użyte quota"""
        current_used = self.quota_state.get('used', 0)
        self.quota_state['used'] = current_used + amount
        self.save_quota_state()
        logger.debug(f"Dodano {amount} do quota, łącznie: {self.quota_state['used']}")
    
    def reset_quota(self):
        """Resetuje quota"""
        self.quota_state = {
            'used': 0,
            'last_reset': datetime.now().isoformat()
        }
        self.save_quota_state()
        logger.info("Quota zostało zresetowane")
    
    def get_quota_state(self) -> Dict:
        """Zwraca stan quota"""
        return self.quota_state
    
    def persist_quota(self, quota_used: int):
        """Zapisuje aktualne zużycie quota"""
        self.quota_state['used'] = quota_used
        self.save_quota_state()
        logger.info(f"Zapisano quota: {quota_used}")
    
    def get_persisted_quota(self) -> int:
        """Zwraca zapisane zużycie quota"""
        return self.quota_state.get('used', 0)
    
    def update_system_state(self, key: str, value):
        """Aktualizuje stan systemu"""
        self.system_state[key] = value
        self.save_system_state()
    
    def get_system_state(self) -> Dict:
        """Zwraca stan systemu"""
        return self.system_state
    
    def clear_all_data(self):
        """Czyści wszystkie dane"""
        try:
            print(f"[CLEAR] Clearing all data from: {self.data_dir.absolute()}")
            logger.info(f"Clearing all data from: {self.data_dir.absolute()}")
            
            # Usuń pliki
            if self.channels_file.exists():
                self.channels_file.unlink()
                print(f"[CLEAR] Deleted: {self.channels_file.absolute()}")
            
            if self.quota_file.exists():
                self.quota_file.unlink()
                print(f"[CLEAR] Deleted: {self.quota_file.absolute()}")
            
            if self.system_state_file.exists():
                self.system_state_file.unlink()
                print(f"[CLEAR] Deleted: {self.system_state_file.absolute()}")
            
            # Resetuj dane w pamięci
            self.channels_data = {}
            self.quota_state = {'used': 0, 'last_reset': datetime.now().isoformat()}
            self.system_state = {
                'last_startup': datetime.now().isoformat(),
                'total_reports_generated': 0,
                'last_report_date': None
            }
            
            print(f"[CLEAR] All data cleared successfully")
            logger.info("All data cleared successfully")
            
        except Exception as e:
            print(f"[CLEAR] Error clearing data: {e}")
            logger.error(f"Error clearing data: {e}")
    
    def get_channel_maps_status(self) -> Dict:
        """Zwraca status map kanałów"""
        return {
            'channel_id_map_count': len(self.channel_id_map),
            'channel_url_map_count': len(self.channel_url_map),
            'channel_id_map_keys': list(self.channel_id_map.keys()),
            'channel_url_map_keys': list(self.channel_url_map.keys()),
            'maps_synchronized': len(self.channel_id_map) == len(self.channel_url_map)
        }
    
    def get_data_stats(self) -> Dict:
        """Zwraca statystyki danych"""
        channels_count = sum(len(channels) for channels in self.channels_data.values())
        categories = list(self.channels_data.keys())
        
        return {
            'data_directory': str(self.data_dir.absolute()),
            'channels_count': channels_count,
            'categories': categories,
            'quota_used': self.quota_state.get('used', 0),
            'quota_last_reset': self.quota_state.get('last_reset'),
            'system_startup': self.system_state.get('last_startup'),
            'files_exist': {
                'channels.json': self.channels_file.exists(),
                'quota_state.json': self.quota_file.exists(),
                'system_state.json': self.system_state_file.exists()
            }
        }

    def add_category(self, category_name: str) -> Dict:
        """Dodaje nową kategorię"""
        try:
            if not category_name or not category_name.strip():
                raise ValueError("Nazwa kategorii nie może być pusta")
            
            category_name = category_name.strip()
            
            if category_name in self.channels_data:
                raise ValueError(f"Kategoria '{category_name}' już istnieje")
            
            # Dodaj nową kategorię
            self.channels_data[category_name] = []
            
            # Zapisz zmiany
            self.save_channels()
            
            print(f"[CATEGORY] Added new category: {category_name}")
            logger.info(f"Added new category: {category_name}")
            
            return {
                'name': category_name,
                'channels_count': 0,
                'message': f'Kategoria "{category_name}" została dodana'
            }
            
        except Exception as e:
            print(f"[CATEGORY] Error adding category: {e}")
            logger.error(f"Error adding category: {e}")
            raise

    def remove_category(self, category_name: str, force: bool = False) -> Dict:
        """Usuwa kategorię"""
        try:
            if category_name not in self.channels_data:
                raise ValueError(f"Kategoria '{category_name}' nie istnieje")
            
            channels_count = len(self.channels_data[category_name])
            
            if channels_count > 0 and not force:
                raise ValueError(
                    f"Kategoria '{category_name}' zawiera {channels_count} kanałów. "
                    "Użyj force=true aby usunąć kategorię wraz z kanałami."
                )
            
            # Usuń kanały z map
            for channel in self.channels_data[category_name]:
                channel_id = channel.get('id')
                channel_url = channel.get('url')
                
                if channel_id in self.channel_id_map:
                    self.channel_id_map.pop(channel_id)
                    print(f"[CATEGORY] Removed from channel_id_map: {channel_id}")
                
                if channel_url in self.channel_url_map:
                    self.channel_url_map.pop(channel_url)
                    print(f"[CATEGORY] Removed from channel_url_map: {channel_url}")
            
            # Usuń kategorię
            del self.channels_data[category_name]
            
            # Zapisz zmiany
            self.save_channels()
            
            print(f"[CATEGORY] Removed category: {category_name} ({channels_count} channels)")
            logger.info(f"Removed category: {category_name} ({channels_count} channels)")
            
            return {
                'name': category_name,
                'channels_count': channels_count,
                'message': f'Kategoria "{category_name}" została usunięta ({channels_count} kanałów)'
            }
            
        except Exception as e:
            print(f"[CATEGORY] Error removing category: {e}")
            logger.error(f"Error removing category: {e}")
            raise

    def get_categories(self) -> List[Dict]:
        """Zwraca listę kategorii z liczbą kanałów i informacją o dostępnych raportach"""
        categories = []
        
        # Sprawdź katalog raportów używając settings
        try:
            from app.config.settings import settings
            reports_dir = settings.reports_path
        except ImportError:
            # Fallback do lokalnego katalogu
            reports_dir = Path("reports")
        
        has_reports_dir = reports_dir.exists()
        
        for category_name, channels in self.channels_data.items():
            # Sprawdź czy są dostępne raporty CSV dla tej kategorii
            has_reports = False
            if has_reports_dir:
                try:
                    # Szukaj plików CSV dla tej kategorii
                    pattern = f"report_{category_name.upper()}_*.csv"
                    csv_files = list(reports_dir.glob(pattern))
                    has_reports = len(csv_files) > 0
                except Exception:
                    has_reports = False
            
            categories.append({
                'name': category_name,
                'channels_count': len(channels),
                'channels': [{'id': c['id'], 'title': c['title']} for c in channels],
                'has_reports': has_reports
            })
        
        return categories

    def _validate_youtube_url(self, url: str) -> bool:
        """Waliduje URL YouTube - akceptuje @handle i /channel/UC..."""
        
        if not url:
            return False
        
        # Sprawdź podstawowy format YouTube
        if not url.startswith('https://www.youtube.com/'):
            return False
        
        # Sprawdź format @handle
        if '@' in url:
            handle_match = re.search(r'youtube\.com/@([a-zA-Z0-9_-]+)', url)
            return handle_match is not None
        
        # Sprawdź format /channel/UC...
        channel_id_match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', url)
        if channel_id_match:
            return True
        
        # Sprawdź inne formaty
        other_patterns = [
            r'youtube\.com/c/[a-zA-Z0-9_-]+',
            r'youtube\.com/user/[a-zA-Z0-9_-]+'
        ]
        
        for pattern in other_patterns:
            if re.search(pattern, url):
                return True
        
        return False 