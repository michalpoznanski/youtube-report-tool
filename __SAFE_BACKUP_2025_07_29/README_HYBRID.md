# YouTube Analyzer Bot - Hybrydowe Rozwiązanie

**Discord Bot + YouTube Data API v3** - Łączy niezawodność YouTube API z wygodą interfejsu Discord.

## 🎯 Zalety tego rozwiązania

### ✅ **Niezawodność YouTube API**
- Bezpośrednie pobieranie z YouTube (bez YAGPDB.xyz)
- Brak opóźnień w dostarczaniu danych
- Pełna kontrola nad danymi
- Stabilne limity API (10,000 jednostek dziennie)

### ✅ **Wygoda interfejsu Discord**
- Znajomy interfejs dla użytkowników
- Komendy tekstowe
- Automatyczne raporty
- Integracja z Google Sheets
- Embedy z podsumowaniami

### ✅ **Organizacja w kategorie (bańki)**
- Grupowanie kanałów według tematów
- Analiza per kategoria
- Łatwe zarządzanie kanałami
- Statystyki per baniek

## 🚀 Instalacja

### 1. Zainstaluj wymagane biblioteki

```bash
pip install -r requirements_yt.txt
python -m spacy download pl_core_news_md
```

### 2. Ustaw zmienne środowiskowe

```bash
# YouTube Data API v3
export YOUTUBE_API_KEY='twój_klucz_youtube_api'

# Discord Bot Token
export DISCORD_TOKEN='twój_token_discord_bota'

# Google Sheets (opcjonalnie)
export SPREADSHEET_ID='id_twojego_arkusza'
```

### 3. Uruchom bota

```bash
python bot_yt_api.py
```

## 📋 Komendy Discord

### 📊 **Raporty**
| Komenda | Opis |
|---------|------|
| `!raport [dni] [kategoria]` | Generuj raport z ostatnich X dni (domyślnie: 7) |
| `!test [dni] [kategoria]` | Test z mniejszym datasetem (domyślnie: 1) |
| `!auto_start` | Uruchom automatyczne raporty co 7 dni |
| `!auto_stop` | Zatrzymaj automatyczne raporty |
| `!status` | Sprawdź status raportów i timing |

### 🏷️ **Zarządzanie kategoriami**
| Komenda | Opis |
|---------|------|
| `!kategorie` | Pokaż dostępne kategorie |
| `!dodaj_kategorie <nazwa>` | Dodaj nową kategorię |
| `!dodaj_kanał <kategoria> <channel_id>` | Dodaj kanał do kategorii |
| `!usun_kanał <kategoria> <channel_id>` | Usuń kanał z kategorii |
| `!lista_kanałów [kategoria]` | Pokaż listę monitorowanych kanałów |

## 🏷️ **Przykłady kategorii (baniek)**

### 🚗 **Motoryzacja**
- Kanały o samochodach, motocyklach, tuning
- Przykłady: Autoblog, Motovlog, Car Reviews

### 🤖 **AI**
- Kanały o sztucznej inteligencji, machine learning
- Przykłady: Two Minute Papers, Lex Fridman, AI News

### ⚽ **Sport**
- Kanały sportowe, relacje, analizy
- Przykłady: ESPN, Sport Channel, Football Analysis

### 🏛️ **Polityka**
- Kanały polityczne, newsy, analizy
- Przykłady: Political News, Analysis Channel

## 🔧 Jak znaleźć Channel ID

1. Przejdź na kanał YouTube
2. Skopiuj URL z paska adresu
3. Channel ID to część po `/channel/`

**Przykład:**
- URL: `https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw`
- Channel ID: `UC_x5XG1OV2P6uZZ5FSM9Ttw`

## 📊 Przykład użycia

### Tworzenie kategorii i dodawanie kanałów:
```
Użytkownik: !dodaj_kategorie Motoryzacja
Bot: ✅ KATEGORIA DODANA
     Nowa kategoria: Motoryzacja
     
     Użyj !dodaj_kanał Motoryzacja <channel_id> aby dodać kanały.

Użytkownik: !dodaj_kanał Motoryzacja UC_x5XG1OV2P6uZZ5FSM9Ttw
Bot: ✅ KANAŁ DODANY
     Kategoria: Motoryzacja
     Channel ID: UC_x5XG1OV2P6uZZ5FSM9Ttw
     Łącznie w kategorii: 1
```

### Generowanie raportów:
```
Użytkownik: !raport 7 Motoryzacja

Bot: 🚀 ROZPOCZYNAM ANALIZĘ
     ⏰ Analizuję ostatnie 7 dni
     🔍 Sprawdzam kategorię 'Motoryzacja' (3 kanałów)...

[Analiza w toku...]

Bot: 📊 PODSUMOWANIE ANALIZY
     📹 Łącznie filmów: 15
     📺 Kanałów: 3
     🏷️ Kategorii: 1
     ⏱️ Shorts: 3
     📺 Long-form: 12
     👥 Unikalnych nazwisk: 8
     👀 Łączne wyświetlenia: 1,234,567
     ❤️ Łączne lajki: 45,678

Bot: 💾 RAPORT ZAPISANY
     [Załącznik: report_Motoryzacja_2024-01-23_15-30.csv]

Bot: 📊 Dane wysłane do Google Sheets
```

### Przeglądanie kategorii:
```
Użytkownik: !kategorie

Bot: 🏷️ DOSTĘPNE KATEGORIE
     🏷️ Motoryzacja: 3 kanałów
     🏷️ AI: 5 kanałów
     🏷️ Sport: 2 kanały
     🏷️ Polityka: 4 kanały
```

## 💰 Koszty API

### YouTube Data API v3
- **Darmowe limity:** 10,000 jednostek dziennie
- **Koszty:** $5 USD za 1,000,000 dodatkowych jednostek
- **Typowe użycie:** ~100-500 jednostek na analizę 10 kanałów

### Przykład obliczeń:
- 10 kanałów × 7 dni = ~70 filmów
- 70 filmów × 2 zapytania = 140 jednostek
- **Koszt:** Darmowe (w ramach limitu)

## 🔄 Migracja z poprzedniej wersji

### Co się zmieniło:
1. **Źródło danych:** YAGPDB.xyz → YouTube Data API v3
2. **Niezawodność:** Znacznie wyższa
3. **Kontrola:** Pełna kontrola nad danymi
4. **Organizacja:** Kategorie kanałów (bańki)
5. **Interfejs:** Ten sam Discord

### Co zostało:
1. **Komendy Discord:** Wszystkie te same + nowe
2. **Google Sheets:** Integracja zachowana
3. **Analiza nazwisk:** spaCy NLP
4. **Automatyczne raporty:** Funkcjonalność zachowana

## 🛠️ Rozwiązywanie problemów

### Błąd: "Brak klucza YouTube API"
```bash
export YOUTUBE_API_KEY='twój_klucz_api'
```

### Błąd: "NIEZNANA KATEGORIA"
```bash
!dodaj_kategorie NazwaKategorii
!dodaj_kanał NazwaKategorii channel_id
```

### Błąd: "Quota exceeded"
- Poczekaj do następnego dnia
- Lub zwiększ limit w Google Cloud Console

### Błąd: "Model spaCy nie znaleziony"
```bash
python -m spacy download pl_core_news_md
```

## 📈 Porównanie z poprzednią wersją

| Aspekt | Stara wersja (YAGPDB) | Nowa wersja (YouTube API) |
|--------|----------------------|---------------------------|
| **Niezawodność** | ❌ Zależność od zewnętrznego serwisu | ✅ Bezpośrednie połączenie z YouTube |
| **Opóźnienia** | ❌ Możliwe opóźnienia | ✅ Dane w czasie rzeczywistym |
| **Kontrola** | ❌ Ograniczona | ✅ Pełna kontrola |
| **Organizacja** | ❌ Pojedyncza lista | ✅ Kategorie (bańki) |
| **Limity** | ❌ Ograniczenia YAGPDB | ✅ Stabilne limity Google |
| **Koszty** | ✅ Darmowe | ✅ Darmowe (w limitach) |
| **Interfejs** | ✅ Discord | ✅ Discord (zachowany) |

## 🎯 Następne kroki

- [ ] Dodanie analizy komentarzy
- [ ] Wykrywanie trendów per kategoria
- [ ] Dashboard webowy
- [ ] Integracja z innymi platformami
- [ ] Analiza sentymentu
- [ ] Eksport do różnych formatów

## 📞 Wsparcie

Jeśli masz pytania lub problemy:
1. Sprawdź logi bota
2. Zweryfikuj klucze API
3. Sprawdź uprawnienia Discord bota
4. Upewnij się, że channel_id są poprawne
5. Użyj `!kategorie` aby sprawdzić dostępne kategorie 