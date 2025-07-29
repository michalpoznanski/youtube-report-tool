#!/usr/bin/env python3
"""
Backup System - Bezpieczne tworzenie kopii zapasowych danych Hook Boost Web
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupSystem:
    def __init__(self):
        self.volume_path = Path("/mnt/volume")
        self.backup_dir = self.volume_path / "backup"
        self.data_dir = self.volume_path / "data"
        self.reports_dir = self.volume_path / "reports"
        
    def create_backup(self):
        """Tworzy pełny backup systemu"""
        try:
            # Utwórz katalog backup z datą
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"manual_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🔒 Rozpoczęcie backupu: {backup_path}")
            
            # 1. Backup plików JSON
            self._backup_json_files(backup_path)
            
            # 2. Backup raportów
            self._backup_reports(backup_path)
            
            # 3. Utwórz plik manifestu
            self._create_manifest(backup_path, timestamp)
            
            # 4. Spakuj backup
            zip_path = self._create_zip_backup(backup_path, backup_name)
            
            # 5. Wyczyść katalog tymczasowy
            shutil.rmtree(backup_path)
            
            logger.info(f"✅ Backup zakończony pomyślnie: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"❌ Błąd podczas tworzenia backupu: {e}")
            raise
    
    def _backup_json_files(self, backup_path: Path):
        """Backup plików JSON z danymi systemu"""
        json_files = [
            ("channels.json", self.data_dir / "channels.json"),
            ("quota_state.json", self.data_dir / "quota_state.json"),
            ("system_state.json", self.data_dir / "system_state.json")
        ]
        
        for name, source_path in json_files:
            if source_path.exists():
                dest_path = backup_path / name
                shutil.copy2(source_path, dest_path)
                logger.info(f"📄 Skopiowano: {name}")
                
                # Sprawdź zawartość
                try:
                    with open(dest_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"   📊 {name}: {len(str(data))} bajtów")
                except Exception as e:
                    logger.warning(f"   ⚠️ Nie można odczytać {name}: {e}")
            else:
                logger.warning(f"⚠️ Plik nie istnieje: {source_path}")
    
    def _backup_reports(self, backup_path: Path):
        """Backup wszystkich raportów"""
        reports_backup_dir = backup_path / "reports"
        reports_backup_dir.mkdir(exist_ok=True)
        
        if self.reports_dir.exists():
            report_files = list(self.reports_dir.glob("*.csv"))
            if report_files:
                for report_file in report_files:
                    dest_file = reports_backup_dir / report_file.name
                    shutil.copy2(report_file, dest_file)
                    logger.info(f"📊 Skopiowano raport: {report_file.name}")
                
                logger.info(f"📁 Skopiowano {len(report_files)} raportów")
            else:
                logger.info("📁 Brak raportów do skopiowania")
        else:
            logger.warning(f"⚠️ Katalog raportów nie istnieje: {self.reports_dir}")
    
    def _create_manifest(self, backup_path: Path, timestamp: str):
        """Tworzy plik manifestu z informacjami o backupie"""
        manifest = {
            "backup_info": {
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "backup_type": "manual_full_backup",
                "version": "1.0"
            },
            "files": {
                "json_files": [],
                "reports": []
            },
            "system_info": {
                "volume_path": str(self.volume_path),
                "data_dir": str(self.data_dir),
                "reports_dir": str(self.reports_dir)
            }
        }
        
        # Dodaj informacje o plikach JSON
        for json_file in backup_path.glob("*.json"):
            manifest["files"]["json_files"].append({
                "name": json_file.name,
                "size": json_file.stat().st_size,
                "modified": datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
            })
        
        # Dodaj informacje o raportach
        reports_dir = backup_path / "reports"
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.csv"):
                manifest["files"]["reports"].append({
                    "name": report_file.name,
                    "size": report_file.stat().st_size,
                    "modified": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
                })
        
        # Zapisz manifest
        manifest_path = backup_path / "backup_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Utworzono manifest: {manifest_path}")
        
        # Wyświetl podsumowanie
        total_files = len(manifest["files"]["json_files"]) + len(manifest["files"]["reports"])
        total_size = sum(f["size"] for f in manifest["files"]["json_files"] + manifest["files"]["reports"])
        
        logger.info(f"📊 Podsumowanie backupu:")
        logger.info(f"   📁 Pliki JSON: {len(manifest['files']['json_files'])}")
        logger.info(f"   📊 Raporty: {len(manifest['files']['reports'])}")
        logger.info(f"   💾 Łączny rozmiar: {total_size} bajtów")
    
    def _create_zip_backup(self, backup_path: Path, backup_name: str) -> Path:
        """Pakuje backup do pliku ZIP"""
        zip_path = self.backup_dir / f"{backup_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in backup_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(backup_path)
                    zipf.write(file_path, arcname)
        
        zip_size = zip_path.stat().st_size
        logger.info(f"📦 Utworzono ZIP: {zip_path} ({zip_size} bajtów)")
        
        return zip_path
    
    def verify_backup(self, backup_path: str):
        """Weryfikuje spójność backupu"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"❌ Plik backupu nie istnieje: {backup_path}")
                return False
            
            # Sprawdź czy to plik ZIP
            if not backup_file.suffix == '.zip':
                logger.error(f"❌ Plik nie jest archiwum ZIP: {backup_path}")
                return False
            
            # Sprawdź zawartość ZIP
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                file_list = zipf.namelist()
                
                # Sprawdź czy są wymagane pliki
                required_files = [
                    'channels.json',
                    'quota_state.json', 
                    'system_state.json',
                    'backup_manifest.json'
                ]
                
                missing_files = [f for f in required_files if f not in file_list]
                if missing_files:
                    logger.error(f"❌ Brakujące pliki w backupie: {missing_files}")
                    return False
                
                logger.info(f"✅ Backup zweryfikowany pomyślnie")
                logger.info(f"📁 Zawiera {len(file_list)} plików")
                logger.info(f"📋 Manifest: {zipf.read('backup_manifest.json').decode('utf-8')}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Błąd podczas weryfikacji backupu: {e}")
            return False

if __name__ == "__main__":
    backup_system = BackupSystem()
    backup_path = backup_system.create_backup()
    backup_system.verify_backup(backup_path) 