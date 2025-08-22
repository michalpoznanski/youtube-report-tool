# 🎯 USTALENIA SYSTEMU YOUTUBE ANALYZER BOT

## 📋 **PODSTAWOWE ZASADY**

### 1. **TYLKO 4 KOMENDY**
- **`!raport`** - tworzy raport CSV na danym pokoju (używa API)
- **`!name`** - analizuje raport pod kątem nazwisk
- **`!help`** - tłumaczy wszystko

### 2. **INTELIGENTNE ROZPOZNAWANIE KONTEKSTU**
- **Automatyczne wykrywanie kategorii** na podstawie nazwy kanału Discord
- **Ważenie nazwisk tylko dla danej kategorii** - nie mieszanie showbiz z politics
- **Kontekstowe analizy** - każdy pokój ma swoje dane

### 3. **KALIBRACJA WAŻENIA NAZWISK**
```
strength = (views_score * 0.5) + (frequency_score * 0.3) + (network_score * 0.2)
```
- **views_score**: wyświetlenia / 1M (max 1.0)
- **frequency_score**: wystąpienia / 10 (max 1.0)  
- **network_score**: liczba kanałów / 5 (max 1.0)

### 4. **PODZIAŁ NA POKOJE DISCORD**
- **Showbiz**: 20 kanałów YouTube
- **Politics**: kanały polityczne
- **Motoryzacja**: kanały motoryzacyjne
- **Podcast**: kanały podcastowe

### 5. **SPÓJNOŚĆ DANYCH**
- **Kolumny CSV**: `Channel_Name`, `View_Count`, `Date_of_Publishing`
- **Format raportów**: JSON z kategorią
- **Struktura plików**: `reports/{kategoria}/youtube_data_{kategoria}_{data}.csv`

### 6. **OPTIMIZACJA WYDAJNOŚCI**
- **spaCy tylko offline** - bot Discord bez spaCy
- **Szybkie analizy** - regex zamiast NLP w bocie
- **Cachowanie modeli** - nie ładowanie za każdym razem

### 7. **ZARZĄDZANIE QUOTA**
- **Smart quota checker** - sprawdzanie przed operacjami
- **Oszczędne operacje** - aktualizacja tylko wyświetleń
- **Ostrzeżenia** - informowanie o limicie

### 8. **LOGGING I DEBUGGING**
- **Bot memory** - zapisywanie błędów i sukcesów
- **Debug mode** - szczegółowe logi podczas testów
- **PID management** - kontrola procesów

### 9. **BEZPIECZEŃSTWO**
- **Token management** - zmienne środowiskowe
- **Error handling** - graceful failures
- **Rate limiting** - ochrona przed spamem

### 10. **USER EXPERIENCE**
- **Polskie komunikaty** - wszystko po polsku
- **Emoji i formatowanie** - czytelne embedy
- **Progres bars** - informowanie o postępie
- **Timeout handling** - reakcje użytkowników

## 🔧 **IMPLEMENTACJA**

### **Mapowanie Kanałów Discord → Kategorie**
```json
{
  "showbiz": ["showbiz", "celebryci", "gwiazdy"],
  "politics": ["politics", "polityka", "sejm"],
  "motoryzacja": ["motoryzacja", "samochody", "auto"],
  "podcast": ["podcast", "rozmowy", "wywiady"]
}
```

### **Algorytm Rozpoznawania Kontekstu**
1. Sprawdź nazwę kanału Discord
2. Znajdź pasującą kategorię
3. Załaduj tylko dane z tej kategorii
4. Analizuj nazwiska w kontekście kategorii

### **Struktura Plików**
```
BOT/
├── reports/
│   ├── showbiz/
│   ├── politics/
│   ├── motoryzacja/
│   └── podcast/
├── channels_config.json
├── bot_yt_api.py
├── analyze_sheet.py
└── USTALENIA_SYSTEMU.md
```

## ✅ **POTWIERDZENIE USTALEŃ**
- [x] Kalibracja ważenia - spójna
- [x] Podział na pokoje - zaimplementowany
- [x] Minimalizm komend - tylko 4 główne
- [x] Inteligentny kontekst - automatyczne wykrywanie
- [x] Optymalizacja - spaCy tylko offline
- [x] Spójność danych - jednolite kolumny CSV
- [x] Quota management - smart checker
- [x] Polish UX - wszystko po polsku 