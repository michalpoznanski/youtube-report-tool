# YouTube Channel Analyzer

Narzędzie w Pythonie do analizy kanałów YouTube z użyciem YouTube Data API v3.

## Funkcjonalności

- 📺 Pobieranie filmów z ostatnich 7 dni z wybranych kanałów
- 🤖 Analiza nazwisk gości używając spaCy (NLP)
- ⏱️ Automatyczne rozpoznawanie Shorts vs Long-form
- 📊 Eksport do CSV z pełnymi danymi
- 📈 Statystyki wyświetleń, lajków, komentarzy
- 🔗 Integracja z Google Sheets (opcjonalnie)

## Instalacja

### 1. Zainstaluj wymagane biblioteki

```bash
pip install -r requirements_yt.txt
```

### 2. Zainstaluj model spaCy dla języka polskiego

```bash
python -m spacy download pl_core_news_md
```

### 3. Uzyskaj klucz YouTube Data API v3

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Włącz YouTube Data API v3
4. Utwórz klucz API w sekcji "Credentials"
5. Skopiuj klucz API

### 4. Ustaw klucz API

```bash
export YOUTUBE_API_KEY='twój_klucz_api'
```

Lub dodaj do pliku `~/.bashrc` lub `~/.zshrc`:
```bash
echo 'export YOUTUBE_API_KEY="twój_klucz_api"' >> ~/.bashrc
source ~/.bashrc
```

## Użytkowanie

### 1. Dodaj kanały do analizy

Edytuj plik `channels.txt` i dodaj channel_id kanałów:

```txt
UC_x5XG1OV2P6uZZ5FSM9Ttw  # Google Developers
UC-lHJZR3Gqxm24_Vd_AJ5Yw  # PewDiePie
```

**Jak znaleźć channel_id:**
- Przejdź na kanał YouTube
- Skopiuj URL z paska adresu
- Channel ID to część po `/channel/`

### 2. Uruchom analizę

```bash
python fetch_report.py
```

### 3. Wyniki

Program utworzy plik CSV z nazwą `report_YYYY-MM-DD_HH-MM.csv` zawierający:

- ID filmu
- Kanał
- Tytuł
- Link
- Data publikacji
- Czy to Short
- Czas trwania (sekundy)
- Nazwiska/Goście (rozpoznane przez AI)
- Liczba wyświetleń
- Lajki
- Komentarze

## Struktura danych

### Kolumny w CSV:

| Kolumna | Opis |
|---------|------|
| ID_filmu | Unikalny identyfikator filmu YouTube |
| Kanał | Nazwa kanału |
| Tytuł | Tytuł filmu |
| Link | URL do filmu |
| Data_publikacji | Data i czas publikacji |
| Czy_Short | "Tak" jeśli film < 60s, "Nie" jeśli dłuższy |
| Czas_trwania_sek | Długość filmu w sekundach |
| Nazwiska_Goście | Rozpoznane nazwiska osób (oddzielone przecinkami) |
| Liczba_wyświetleń | Liczba wyświetleń |
| Lajki | Liczba lajków |
| Komentarze | Liczba komentarzy |

## Limity API

- **Darmowe limity:** 10,000 jednostek dziennie
- **Koszty:** $5 USD za 1,000,000 dodatkowych jednostek
- **Typowe użycie:** ~100-500 jednostek na analizę 10 kanałów

## Rozwiązywanie problemów

### Błąd: "Model spaCy nie znaleziony"
```bash
python -m spacy download pl_core_news_md
```

### Błąd: "Brak klucza API"
```bash
export YOUTUBE_API_KEY='twój_klucz_api'
```

### Błąd: "Kanał nie istnieje"
Sprawdź czy channel_id jest poprawny w pliku `channels.txt`

### Błąd: "Quota exceeded"
Poczekaj do następnego dnia lub zwiększ limit w Google Cloud Console

## Przykład użycia

```bash
# Ustaw klucz API
export YOUTUBE_API_KEY='AIzaSyC...'

# Uruchom analizę
python fetch_report.py

# Wynik:
# 🎬 YouTube Channel Analyzer
# ==================================================
# ✅ Model spaCy załadowany
# 📺 Załadowano 3 kanałów z channels.txt
# 
# 🚀 Rozpoczynam analizę 3 kanałów...
# 
# 📺 Analizuję kanał: UC_x5XG1OV2P6uZZ5FSM9Ttw
# 🔍 Pobieram filmy z kanału UC_x5XG1OV2P6uZZ5FSM9Ttw od 2024-01-16T10:00:00Z
# 📹 Znaleziono 5 filmów z ostatnich 7 dni
#   ✅ Google I/O 2024 - Day 1 Keynote...
#   ✅ Building AI-powered apps with Gemini...
# 
# 📊 PODSUMOWANIE ANALIZY:
#   📹 Łącznie filmów: 15
#   📺 Kanałów: 3
#   ⏱️  Shorts: 3
#   📺 Long-form: 12
#   👥 Unikalnych nazwisk: 8
#   👀 Łączne wyświetlenia: 1,234,567
#   ❤️  Łączne lajki: 45,678
# 
# 💾 Raport zapisany jako: report_2024-01-23_15-30.csv
# 
# ✅ Analiza zakończona! Plik: report_2024-01-23_15-30.csv
# 📊 Przeanalizowano 15 filmów z 3 kanałów
```

## Następne kroki

- [ ] Dodanie eksportu do Google Sheets
- [ ] Analiza komentarzy
- [ ] Wykrywanie trendów
- [ ] Automatyczne uruchamianie (cron)
- [ ] Dashboard webowy 