# 🚀 Uniwersalny System Analizy YouTube

Połączony system do analizy danych z YouTube, zawierający dwa boty:
- **Bot YT2** - Analiza słów kluczowych z tytułów
- **Bot analizy nazwisk** - Analiza nazwisk z filmów

## 📁 Struktura projektu

```
📁 BOT/
├── 📁 shared/                    # Wspólne moduły
│   ├── 📄 google_sheets.py      # Pobieranie z Google Sheets
│   ├── 📄 text_analyzer.py      # Analiza tekstu
│   └── 📄 report_generator.py   # Generowanie raportów
├── 📄 yt_analyzer.py            # Bot analizy słów kluczowych
├── 📄 name_analyzer.py          # Bot analizy nazwisk
├── 📄 main.py                   # Główny interfejs
├── 📄 credentials.json          # Dane uwierzytelniające
└── 📄 requirements.txt          # Zależności
```

## 🛠️ Instalacja

1. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

2. **Zainstaluj model spaCy:**
```bash
python -m spacy download pl_core_news_md
```

3. **Skonfiguruj credentials.json** (skopiuj z drugiego projektu)

## 🚀 Użycie

### Główny interfejs
```bash
python main.py <link_do_arkusza_google_sheets>
```

### Bezpośrednie uruchomienie

**Analiza słów kluczowych:**
```bash
python yt_analyzer.py <link_do_arkusza>
```

**Analiza nazwisk:**
```bash
python name_analyzer.py <link_do_arkusza>
```

## 📊 Funkcjonalności

### 🤖 Bot YT2 - Analiza słów kluczowych
- ✅ Pobiera dane z Google Sheets
- ✅ Dzieli filmy na Shorts i Long-form
- ✅ Wyciąga najpopularniejsze słowa kluczowe
- ✅ Usuwa polskie stopwords
- ✅ Generuje raporty CSV

### 👥 Bot analizy nazwisk
- ✅ Analizuje nazwiska z filmów
- ✅ Oblicza wskaźniki siły
- ✅ Uwzględnia wagę czasową
- ✅ Analizuje wpływ kanałów
- ✅ Boost za Shortsy

### 🔧 Wspólne moduły
- ✅ Uniwersalne pobieranie z Google Sheets
- ✅ Wspólne funkcje analizy tekstu
- ✅ System generowania raportów
- ✅ Kod wielokrotnego użytku

## 📈 Przykładowe raporty

### Analiza słów kluczowych
```
=== Analiza słów kluczowych YT ===
Data generowania: 2024-01-15 14:30:25

--- SHORTS ---
 1. polityka              -  45 wystąpień
 2. wybory                -  32 wystąpień
 3. rząd                  -  28 wystąpień

--- LONG-FORM ---
 1. rozmowa               -  67 wystąpień
 2. gość                  -  54 wystąpień
 3. wywiad                -  43 wystąpień
```

### Analiza nazwisk
```
=== Filmy ===
+----------------+----------------+-------------------+---------------------+------------------------+
| Nazwisko/Ksywa | Liczba filmów | Suma wyświetleń  | Średnia wyświetleń | Wskaźnik siły (0-100) |
+----------------+----------------+-------------------+---------------------+------------------------+
| mentzen        |             12 |         2,450,000 |             204,167 |                   95.2 |
| biedrzycka     |              8 |         1,890,000 |             236,250 |                   87.3 |
+----------------+----------------+-------------------+---------------------+------------------------+
```

## 🔧 Konfiguracja

### Google Sheets
Upewnij się, że arkusz zawiera kolumny:
- `Title` - tytuł filmu
- `Category` - kategoria (opcjonalnie)
- `Wyświetlenia` - liczba wyświetleń (dla analizy nazwisk)
- `Date of Publishing` - data publikacji (dla analizy nazwisk)
- `Channel Name` - nazwa kanału (dla analizy nazwisk)

## 🎯 Korzyści połączenia

- ✅ **Kod wielokrotnego użytku**
- ✅ **Łatwiejsze utrzymanie**
- ✅ **Spójny system raportowania**
- ✅ **Możliwość dodawania nowych typów analiz**
- ✅ **Wspólne moduły i funkcje**

## 🚀 Rozwój

System jest zaprojektowany do łatwego rozszerzania:
- Dodawanie nowych typów analiz
- Nowe formaty raportów
- Dodatkowe źródła danych
- Integracja z innymi API 