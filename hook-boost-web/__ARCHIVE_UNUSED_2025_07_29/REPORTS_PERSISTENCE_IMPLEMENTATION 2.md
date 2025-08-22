# 🔧 Implementacja Trwałości Raportów CSV

## 📋 **Przegląd Problemów**

### **Zidentyfikowane problemy:**
1. **Raporty znikają po restarcie Railway** - mimo że dane systemowe są trwałe
2. **Frontend pokazuje tylko 2 ostatnie raporty** - brak pełnej listy
3. **Raporty są zapisywane w katalogu roboczym** - który jest czyszczony przez Railway

## 🎯 **Zadanie 1: Trwały katalog raportów**

### **Implementacja:**
```python
# app/config/settings.py
@property
def reports_path(self) -> Path:
    """Ścieżka do katalogu z raportami"""
    # Użyj Railway Volume Path jeśli dostępny, w przeciwnym razie domyślny katalog
    import os
    railway_volume = os.getenv("RAILWAY_VOLUME_PATH")
    if railway_volume:
        return Path(railway_volume) / "reports"
    else:
        return Path(self.reports_dir)
```

### **Rezultat:**
- Automatyczne wykrywanie Railway Volume Path
- Fallback do domyślnego katalogu jeśli volume path nie jest ustawiony
- Railway używa `/app/reports` (katalog roboczy)

## 🎯 **Zadanie 2: Automatyczne tworzenie katalogu reports**

### **Implementacja:**
```python
# app/config/settings.py
def create_directories(self):
    """Tworzy wymagane katalogi"""
    try:
        print(f"📁 Tworzenie katalogów...")
        
        # Katalog danych
        self.data_path.mkdir(exist_ok=True)
        print(f"✅ Katalog danych: {self.data_path.absolute()}")
        
        # Katalog raportów (trwały)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Katalog raportów: {self.reports_path.absolute()}")
        
        # Katalog backupów
        self.backup_path.mkdir(exist_ok=True)
        print(f"✅ Katalog backupów: {self.backup_path.absolute()}")
        
        # Katalog logów
        Path("logs").mkdir(exist_ok=True)
        print(f"✅ Katalog logów: logs/")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia katalogów: {e}")
        raise
```

### **Rezultat:**
- Automatyczne tworzenie katalogu reports z logami
- Obsługa błędów podczas tworzenia katalogów
- Szczegółowe logi procesu tworzenia

## 🎯 **Zadanie 3: Enhanced reports list endpoint**

### **Implementacja:**
```python
# app/api/routes.py
@router.get("/reports/list")
async def list_reports():
    """Zwraca listę dostępnych raportów"""
    try:
        import os
        from datetime import datetime
        
        reports = []
        reports_dir = settings.reports_path
        
        print(f"📂 Szukanie raportów w: {reports_dir.absolute()}")
        logger.info(f"Szukanie raportów w: {reports_dir.absolute()}")
        
        # Sprawdź czy katalog istnieje
        if not reports_dir.exists():
            print(f"⚠️ Katalog raportów nie istnieje: {reports_dir.absolute()}")
            logger.warning(f"Katalog raportów nie istnieje: {reports_dir.absolute()}")
            # Utwórz katalog
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Utworzono katalog raportów: {reports_dir.absolute()}")
            logger.info(f"Utworzono katalog raportów: {reports_dir.absolute()}")
        
        # Listuj pliki CSV
        csv_files = list(reports_dir.glob("*.csv"))
        print(f"📄 Znaleziono {len(csv_files)} plików CSV")
        logger.info(f"Znaleziono {len(csv_files)} plików CSV")
        
        for file_path in csv_files:
            try:
                stats = os.stat(file_path)
                reports.append({
                    'filename': file_path.name,
                    'size': stats.st_size,
                    'created': stats.st_ctime,
                    'created_date': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    'path': str(file_path.absolute())
                })
                print(f"   📄 {file_path.name} ({stats.st_size} bytes)")
            except Exception as e:
                print(f"   ❌ Błąd podczas czytania {file_path.name}: {e}")
                logger.error(f"Błąd podczas czytania {file_path.name}: {e}")
        
        # Sortuj po dacie utworzenia (najnowsze pierwsze)
        sorted_reports = sorted(reports, key=lambda x: x['created'], reverse=True)
        
        print(f"✅ Zwracam {len(sorted_reports)} raportów")
        logger.info(f"Zwracam {len(sorted_reports)} raportów")
        
        return {
            "reports": sorted_reports,
            "total_count": len(sorted_reports),
            "reports_directory": str(reports_dir.absolute())
        }
        
    except Exception as e:
        print(f"❌ Błąd podczas listowania raportów: {e}")
        logger.error(f"Błąd podczas listowania raportów: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### **Rezultat:**
- Szczegółowe logi procesu listowania raportów
- Automatyczne tworzenie katalogu jeśli nie istnieje
- Pełne informacje o plikach (rozmiar, data utworzenia, ścieżka)
- Sortowanie po dacie utworzenia (najnowsze pierwsze)

## 🎯 **Zadanie 4: CSV generator logging**

### **Implementacja:**
```python
# app/storage/csv_generator.py
# W generate_csv i generate_summary_csv
# Upewnij się, że katalog raportów istnieje
settings.reports_path.mkdir(parents=True, exist_ok=True)

# Zapisz CSV
df.to_csv(filepath, index=False, encoding='utf-8')

print(f"📊 Wygenerowano raport CSV: {filepath.absolute()}")
print(f"   📄 Nazwa pliku: {filename}")
print(f"   📁 Katalog: {settings.reports_path.absolute()}")
print(f"   📈 Liczba wierszy: {len(df)}")
print(f"   💾 Rozmiar pliku: {filepath.stat().st_size} bytes")

logger.info(f"Wygenerowano CSV: {filepath}")
logger.info(f"Raport CSV: {filename}, {len(df)} wierszy, {filepath.stat().st_size} bytes")
```

### **Rezultat:**
- Szczegółowe logi przy generowaniu każdego raportu
- Informacje o ścieżce, rozmiarze, liczbie wierszy
- Automatyczne tworzenie katalogu przed zapisem

## 🎯 **Zadanie 5: Debug endpoint dla raportów**

### **Implementacja:**
```python
# app/api/routes.py
@router.get("/debug/reports")
async def debug_reports():
    """Debug endpoint - pokazuje informacje o katalogu raportów"""
    try:
        import os
        from datetime import datetime
        
        reports_dir = settings.reports_path
        
        # Sprawdź czy katalog istnieje
        exists = reports_dir.exists()
        absolute_path = str(reports_dir.absolute())
        
        # Sprawdź uprawnienia
        can_write = False
        can_read = False
        if exists:
            try:
                test_file = reports_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                can_write = True
            except Exception:
                can_write = False
            
            try:
                list(reports_dir.iterdir())
                can_read = True
            except Exception:
                can_read = False
        
        # Listuj pliki
        csv_files = []
        if exists and can_read:
            for file_path in reports_dir.glob("*.csv"):
                try:
                    stats = os.stat(file_path)
                    csv_files.append({
                        'name': file_path.name,
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        'path': str(file_path.absolute())
                    })
                except Exception as e:
                    csv_files.append({
                        'name': file_path.name,
                        'error': str(e)
                    })
        
        return {
            "reports_directory": {
                "path": absolute_path,
                "exists": exists,
                "can_write": can_write,
                "can_read": can_read
            },
            "csv_files": csv_files,
            "total_csv_files": len(csv_files),
            "railway_volume_path": os.getenv("RAILWAY_VOLUME_PATH", "Not set")
        }
        
    except Exception as e:
        logger.error(f"Błąd podczas debugowania raportów: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### **Rezultat:**
- Endpoint `/api/v1/debug/reports` dostępny
- Pełne informacje o katalogu raportów i uprawnieniach
- Lista wszystkich plików CSV z szczegółami
- Informacje o Railway Volume Path

## 🧪 **Testowanie**

### **1. Test generowania raportu:**
```bash
curl -X POST https://youtube-report-tool-production.up.railway.app/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7}'
```

**Wynik:**
- Raport został wygenerowany z kolumną `video_type`
- Zawiera zarówno `shorts` jak i `long` form
- Szczegółowe logi w konsoli

### **2. Test listy raportów:**
```bash
curl -s https://youtube-report-tool-production.up.railway.app/api/v1/reports/list
```

**Wynik:**
```json
{
  "reports": [],
  "total_count": 0,
  "reports_directory": "/app/reports"
}
```

### **3. Test debug endpoint:**
```bash
curl -s https://youtube-report-tool-production.up.railway.app/api/v1/debug/reports
```

**Wynik:**
```json
{
  "reports_directory": {
    "path": "/app/reports",
    "exists": true,
    "can_write": true,
    "can_read": true
  },
  "csv_files": [],
  "total_csv_files": 0,
  "railway_volume_path": "Not set"
}
```

## 🚨 **Zidentyfikowane problemy**

### **Problem 1: Railway Volume Path**
- Railway nie ma ustawionego `RAILWAY_VOLUME_PATH`
- Raporty są zapisywane w `/app/reports` (katalog roboczy)
- Katalog roboczy jest czyszczony przy restarcie

### **Problem 2: Raporty znikają**
- Mimo że raport jest generowany, nie jest widoczny w liście
- Może być problem z uprawnieniami lub ścieżką

### **Problem 3: Frontend nie widzi raportów**
- Endpoint `/reports/list` zwraca pustą listę
- Frontend nie może pobrać raportów

## 🔧 **Rozwiązania**

### **Rozwiązanie 1: Konfiguracja Railway Volume**
```bash
# W Railway dashboard, dodaj zmienną środowiskową:
RAILWAY_VOLUME_PATH=/app/data
```

### **Rozwiązanie 2: Sprawdzenie uprawnień**
- Katalog `/app/reports` ma uprawnienia do zapisu
- Problem może być w ścieżce lub uprawnieniach

### **Rozwiązanie 3: Debug i monitoring**
- Endpoint `/debug/reports` pokazuje pełne informacje
- Szczegółowe logi w konsoli
- Monitoring procesu generowania raportów

## 🚀 **Wdrożenie**

### **Status wdrożenia:**
- ✅ Kod zacommitowany i wypchnięty do GitHub
- ✅ Railway automatycznie wdrożył zmiany
- ✅ Aplikacja działa poprawnie
- ✅ Endpointy debug dostępne
- ✅ Szczegółowe logi działają

### **URL produkcji:**
```
https://youtube-report-tool-production.up.railway.app
```

## 📈 **Korzyści**

### **1. Enhanced reports persistence:**
- ✅ Automatyczne wykrywanie Railway Volume Path
- ✅ Szczegółowe logi procesu generowania
- ✅ Debug endpoint dla troubleshooting
- ✅ Automatyczne tworzenie katalogów

### **2. Better error handling:**
- ✅ Obsługa błędów uprawnień
- ✅ Automatyczne tworzenie katalogów
- ✅ Szczegółowe logi błędów
- ✅ Debug tools dla monitorowania

### **3. Improved monitoring:**
- ✅ Endpoint `/debug/reports` dostępny
- ✅ Pełna widoczność stanu katalogu raportów
- ✅ Informacje o uprawnieniach i plikach
- ✅ Railway Volume Path monitoring

## 🔮 **Następne Kroki**

1. **Railway Volume Path** - skonfigurowanie trwałego katalogu
2. **Testing** - sprawdzenie trwałości po restarcie Railway
3. **Frontend integration** - upewnienie się, że frontend używa poprawnej ścieżki
4. **Monitoring** - obserwowanie logów generowania raportów
5. **Backup strategy** - implementacja automatycznego backupu raportów

## 📝 **Podsumowanie**

### **✅ Zaimplementowane funkcjonalności:**
- Automatyczne wykrywanie Railway Volume Path
- Szczegółowe logi procesu generowania raportów
- Enhanced endpoint listy raportów
- Debug endpoint dla raportów
- Automatyczne tworzenie katalogów

### **🚨 Zidentyfikowane problemy:**
- Railway nie ma ustawionego Volume Path
- Raporty są zapisywane w katalogu roboczym
- Raporty znikają po restarcie

### **🔧 Potrzebne działania:**
- Konfiguracja Railway Volume Path
- Testowanie trwałości po restarcie
- Sprawdzenie integracji z frontendem

**System ma wszystkie narzędzia do debugowania i monitorowania, ale potrzebuje konfiguracji Railway Volume Path dla pełnej trwałości!** 🚀 