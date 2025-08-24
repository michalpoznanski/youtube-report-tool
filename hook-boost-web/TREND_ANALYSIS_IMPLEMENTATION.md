# 📊 Implementacja Automatycznej Analizy Trendów

## 🎯 Cel

Rozwiązanie problemu z brakiem danych na podstronie "📈 Raport Podcast" poprzez automatyczne analizowanie plików CSV generowanych codziennie o 1 w nocy przez scheduler.

## 🔧 Co zostało zaimplementowane

### 1. Automatyczna Analiza w Schedulerze
- **Lokalizacja**: `app/scheduler/task_scheduler.py`
- **Funkcjonalność**: Po wygenerowaniu pliku CSV, scheduler automatycznie uruchamia analizę
- **Kod**: Dodano wywołanie `auto_analyze_and_save(category)` po `generate_csv()`

### 2. Rozszerzony Trend Store
- **Lokalizacja**: `app/trend/core/store/trend_store.py`
- **Nowe funkcje**:
  - `auto_analyze_and_save()` - automatyczna analiza i zapis
  - `analyze_all_existing_csvs()` - analiza wszystkich istniejących CSV
  - `force_reanalyze_category()` - wymuszenie ponownej analizy
  - `get_latest_analysis()` - pobieranie najnowszej analizy
  - `get_analysis_for_date()` - pobieranie analizy dla konkretnej daty

### 3. Zaktualizowany Router Trendów
- **Lokalizacja**: `app/trend/routers/router.py`
- **Zmiany**: Router teraz używa `trend_store` zamiast bezpośrednio `CSVProcessor`
- **Fallback**: Jeśli brak przeanalizowanych danych, używa CSVProcessor

### 4. Nowe Endpointy API
- **Główny API**: `/api/v1/trends/analyze-all` (POST)
- **Główny API**: `/api/v1/trends/{category}/reanalyze` (POST)
- **Trend API**: `/trend/api/trends/{category}` (GET)
- **Trend API**: `/trend/api/trends/{category}/dates` (GET)

### 5. Interfejs Użytkownika
- **Strona główna**: Dodano sekcję "📊 Analiza Trendów" z przyciskami
- **Podstrona trendów**: Dodano przyciski do ręcznego uruchomienia analizy
- **Status**: Komunikaty o postępie i wynikach operacji

## 🚀 Jak to działa

### Automatycznie (codziennie o 1 w nocy)
1. Scheduler generuje pliki CSV dla każdej kategorii
2. Automatycznie uruchamia analizę każdego pliku CSV
3. Wyniki analizy zapisywane są w `trend_store` jako pliki JSON
4. Dane są dostępne natychmiast po analizie

### Ręcznie (przez UI)
1. Użytkownik klika przycisk "🔄 Analizuj wszystkie pliki CSV"
2. System analizuje wszystkie istniejące pliki CSV
3. Wyniki zapisywane są w `trend_store`
4. Strona automatycznie się odświeża z nowymi danymi

## 📁 Struktura plików wynikowych

```
/mnt/volume/guest_analysis/trends/
├── podcast/
│   ├── video_trends.json          # Najnowsze trendy
│   ├── video_growth_2025-08-13.json  # Dane wzrostu dla konkretnej daty
│   └── stats_2025-08-13.json     # Statystyki dla konkretnej daty
├── motoryzacja/
│   └── ...
└── polityka/
    └── ...
```

## 🔍 Rozwiązywanie problemów

### Problem: Brak danych na podstronie trendów
**Rozwiązanie**: Uruchom analizę ręcznie:
1. Przejdź na stronę główną
2. Kliknij "🔄 Analizuj wszystkie pliki CSV"
3. Poczekaj na zakończenie analizy
4. Odśwież podstronę trendów

### Problem: Dane są przestarzałe
**Rozwiązanie**: Wymuś ponowną analizę:
1. Na podstronie trendów kliknij "🔄 Przeanalizuj ponownie [Kategoria]"
2. Lub na stronie głównej użyj przycisków dla konkretnych kategorii

### Problem: Błąd podczas analizy
**Sprawdź**:
1. Czy pliki CSV istnieją w `/mnt/volume/reports/`
2. Czy pliki CSV mają poprawną strukturę (kolumny: Video_ID, Title, View_Count, Duration)
3. Logi aplikacji w konsoli

## 🧪 Testowanie

Uruchom test funkcjonalności:
```bash
cd hook-boost-web
python test_trend_analysis.py
```

## 📊 Monitorowanie

### Logi automatycznej analizy
- `🔄 Auto-analiza: Rozpoczynam analizę dla [KATEGORIA]`
- `✅ Auto-analiza: Wczytano [X] wideo dla [KATEGORIA]`
- `✅ Auto-analiza: Zakończono analizę i zapisano wyniki`

### Status w UI
- Komunikaty o postępie analizy
- Liczba przetworzonych plików
- Liczba pomyślnie przeanalizowanych plików
- Błędy z opisem problemu

## 🔄 Przepływ danych

```
CSV Files (1:00 AM) → Scheduler → Auto Analysis → Trend Store → UI Display
     ↓
Manual Trigger → Analysis → Trend Store → UI Display
```

## ✅ Korzyści

1. **Automatyczne**: Dane dostępne natychmiast po wygenerowaniu CSV
2. **Ręczne**: Możliwość analizy istniejących plików w dowolnym momencie
3. **Wydajne**: Analiza wykonywana tylko raz, wyniki cachowane
4. **Niezawodne**: Fallback do CSVProcessor jeśli brak przeanalizowanych danych
5. **Przejrzyste**: Status operacji w czasie rzeczywistym

## 🚨 Uwagi

- Analiza może potrwać kilka minut dla dużej liczby plików
- Pliki JSON w `trend_store` są automatycznie czyszczone po 7 dniach
- W przypadku błędu analizy, system używa fallback do CSVProcessor
- Wszystkie operacje są logowane dla celów debugowania
