# Trend Services - CSV Processor

## 📋 Opis

`CSVProcessor` to niezawodny serwis do przetwarzania danych z raportów CSV dla modułu trend. Zapewnia bezpieczne wczytywanie plików CSV, obliczanie przyrostów (delta) i klasyfikację wideo.

## 🚀 Główne funkcjonalności

### 1. Bezpieczne wczytywanie CSV
- Obsługa błędów `FileNotFoundError`
- Obsługa błędów parsowania CSV
- Obsługa błędów kodowania UTF-8
- Walidacja wymaganych kolumn

### 2. Obliczanie przyrostów (Delta)
- Porównanie dzisiejszych i wczorajszych wyświetleń
- Sortowanie malejąco według przyrostu
- Top 50 wyników

### 3. Klasyfikacja wideo
- **Shorts**: ≤ 60 sekund
- **Longform**: > 60 sekund

### 4. Dodatkowe metadane
- Thumbnail URL (YouTube)
- Channel name
- Duration w sekundach

## 📁 Struktura plików

```
app/trend/services/
├── __init__.py              # Eksport funkcji
├── csv_processor.py         # Główny serwis
├── test_csv_processor.py    # Test funkcjonalności
└── README.md               # Ta dokumentacja
```

## 🔧 Użycie

### Podstawowe użycie

```python
from app.trend.services import get_trend_data
from datetime import date

# Pobierz dane trendów dla PODCAST z dzisiejszą datą
trend_data = get_trend_data("PODCAST", date.today())

# Wynik to lista słowników z kluczami:
# - title: tytuł wideo
# - views: dzisiejsze wyświetlenia
# - delta: przyrost (dzisiaj - wczoraj)
# - video_type: "Shorts" lub "Longform"
# - thumbnail_url: URL miniaturki YouTube
# - video_id: ID wideo YouTube
# - channel: nazwa kanału
# - duration_seconds: czas trwania w sekundach
```

### Zaawansowane użycie

```python
from app.trend.services import CSVProcessor

processor = CSVProcessor()

# Sprawdź dostępne daty
available_dates = processor.get_available_dates("PODCAST")

# Pobierz dane dla konkretnej daty
trend_data = processor.get_trend_data("PODCAST", date.fromisoformat("2025-08-13"))
```

## ⚙️ Konfiguracja

### Ścieżka do raportów
Serwis używa stałej ścieżki: `/mnt/volume/reports`

### Format nazw plików
```
report_{CATEGORY}_{YYYY-MM-DD}.csv
```

**Przykłady:**
- `report_PODCAST_2025-08-13.csv`
- `report_MOTO_2025-08-13.csv`
- `report_POLITYKA_2025-08-13.csv`

## 🧪 Testowanie

Uruchom test funkcjonalności:

```bash
cd app/trend/services
python test_csv_processor.py
```

## 🛡️ Obsługa błędów

Serwis obsługuje następujące scenariusze błędów:

1. **Plik nie istnieje** → Zwraca pustą listę `[]`
2. **Błąd parsowania CSV** → Loguje błąd, zwraca `[]`
3. **Brak wymaganych kolumn** → Loguje błąd, zwraca `[]`
4. **Pusty plik CSV** → Loguje ostrzeżenie, zwraca `[]`
5. **Błąd kodowania** → Loguje błąd, zwraca `[]`

## 📊 Wymagane kolumny CSV

Plik CSV musi zawierać następujące kolumny:

- `video_id` - Unikalny identyfikator wideo YouTube
- `title` - Tytuł wideo
- `views_today` - Liczba wyświetleń dzisiaj
- `duration_seconds` - Czas trwania w sekundach
- `channel` - Nazwa kanału (opcjonalna)

## 🔄 Logika przetwarzania

1. **Wczytanie danych**: Dzisiejszy i wczorajszy raport
2. **Klasyfikacja**: Shorts vs Longform na podstawie czasu trwania
3. **Obliczenie delta**: `views_today - views_yesterday`
4. **Sortowanie**: Malejąco według delta
5. **Limit**: Top 50 wyników
6. **Wzbogacenie**: Thumbnail URL, dodatkowe metadane

## 📝 Logi

Serwis używa standardowego modułu `logging` z następującymi poziomami:

- **DEBUG**: Szczegóły wczytywania plików
- **INFO**: Informacje o pomyślnym przetwarzaniu
- **WARNING**: Ostrzeżenia (puste pliki, brak wczorajszych danych)
- **ERROR**: Błędy parsowania, kodowania, brakujące kolumny

## 🚀 Integracja z istniejącym kodem

Serwis jest zaprojektowany jako zamiennik dla istniejących funkcji w:
- `app/trend/core/loader.py`
- `app/trend/utils/report_loader.py`

Może być używany w routerach trend (`app/trend/routers/router.py`) do zastąpienia obecnej logiki ładowania CSV.
