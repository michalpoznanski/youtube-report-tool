# 🚀 HOOK BOOST 3.0 - ULTRA LEAN

Discord bot do monitorowania kanałów YouTube i generowania surowych danych.
Ultra-lekki, modularny, zero analizy - tylko surowe dane.

## 📋 FUNKCJONALNOŚCI

### 🎯 **Główne Komendy:**
- `!śledź` - Dodawanie kanałów YouTube do pokoju
- `!raport` - Generowanie 17-kolumnowego CSV
- `!status` - Status systemu
- `!pomoc` - Lista komend
- `!scheduler` - Status automatyzacji
- `!git` - Status GitHub integration

### 📊 **17 Kolumn CSV:**
1. Channel_Name
2. Date_of_Publishing
3. Hour_GMT2
4. Title
5. Description
6. Tags
7. Video_Type (shorts vs long)
8. View_Count
9. Like_Count
10. Comment_Count
11. Favorite_Count
12. Definition
13. Has_Captions
14. Licensed_Content
15. Topic_Categories
16. Names_Extracted
17. Video_ID

## 🔧 INSTALACJA

### 1. Przygotowanie środowiska
```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Ustaw zmienne środowiskowe
export DISCORD_TOKEN="your_discord_token"
export YOUTUBE_API_KEY="your_youtube_api_key"
```

### 2. Uruchomienie
```bash
python main.py
```

## 📁 STRUKTURA PROJEKTU

```
HOOK_BOOST_3.0/
├── main.py                    # Bot Discord
├── modules/
│   ├── sledz_system.py       # System !śledź
│   ├── raport_system.py      # System !raport (17 kolumn)
│   ├── config_manager.py     # Zarządzanie konfiguracją
│   ├── scheduler.py          # Automatyczne raporty
│   └── git_manager.py        # GitHub integration
├── data/
│   ├── channels_config.json  # Konfiguracja kanałów
│   └── raw_data/            # Raporty CSV
│       └── YYYY-MM-DD/      # Struktura dzienna
├── requirements.txt
├── Dockerfile               # Container deployment
└── README.md
```

## 🎮 PRZYKŁADY UŻYCIA

### Dodawanie kanałów:
```
# W pokoju #showbiz
!śledź
https://www.youtube.com/@TVP_INFO
https://www.youtube.com/@PolsatNews
UCvHFbkohgX29NhaUtmkzLmg
```

### Generowanie raportu:
```
!raport
# Tworzy plik: data/raw_data/2025-01-27/showbiz_2025-01-27.csv
```

## ⚙️ KONFIGURACJA

### Zmienne środowiskowe:
- `DISCORD_TOKEN` - Token bota Discord
- `YOUTUBE_API_KEY` - Klucz YouTube Data API v3
- `GITHUB_TOKEN` - Token GitHub (dla auto-commit)

### Quota Management:
- **ULTRA LEAN MODE** - brak monitorowania quota
- Sprawdzaj quota na stronie Google Console
- Koszty operacji:
  - `!śledź` @handle: 1 quota
  - `!śledź` Channel ID: 0 quota
  - `!raport` per film: 1 quota

### Automatyzacja:
- **Codzienne raporty** o 06:00 UTC
- **Automatyczny commit** do GitHub
- **HTTP server** na porcie 8000 (Render.com)

## 🎯 FILOZOFIA ULTRA LEAN

- **Zero analizy** - tylko surowe dane
- **Modularność** - łatwa rozbudowa
- **Ultra lean** - bez monitorowania quota
- **Multi-room** - każdy pokój = kategoria
- **Auto-commit** - raporty do GitHub

## 📈 ROADMAP

### Faza 1 (CURRENT): ✅
- [x] Bot Discord z komendami
- [x] System !śledź
- [x] System !raport (17 kolumn)
- [x] Quota management
- [x] Struktura dzienna CSV

### Faza 2 (NEXT):
- [ ] System śledzenia dynamiki (3 dni)
- [ ] Auto-commit do GitHub
- [ ] Scheduler (codzienne raporty)
- [ ] Railway deployment

### Faza 3 (FUTURE):
- [ ] Analiza viral score
- [ ] Alerty o trendach
- [ ] Dashboard web
- [ ] API endpoint

---

**🚀 HOOK BOOST 3.0 - Built with ❤️ in 2025** 