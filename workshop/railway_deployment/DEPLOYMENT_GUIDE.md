# 🚂 RAILWAY DEPLOYMENT GUIDE

## 📁 STRUKTURA GOTOWA:
```
hook_boost_railway/
├── main.py                     # Bot Discord (Hook Boost V2)
├── scheduler.py                # Automatyczne codzienne raporty
├── Dockerfile                  # Railway container
├── requirements.txt            # Dependencies
├── railway.json                # Railway config
├── raport_system_workshop.py   # System raportów (24h)
├── sledz_system.py             # System śledzenia kanałów
├── quota_manager.py            # Monitorowanie quota
├── channels_config.json        # Konfiguracja kanałów
└── raw_data/                   # Folder na codzienne dane

```

## 🚀 DEPLOYMENT STEPS:

### 1. ZAŁÓŻ KONTO RAILWAY
- Idź na https://railway.app
- Zaloguj się przez GitHub
- Verify email

### 2. UTWÓRZ NOWY PROJEKT
- New Project → Deploy from GitHub repo
- Wybierz repo z kodem hook_boost_railway/

### 3. USTAW ENVIRONMENT VARIABLES
```
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
RAILWAY_ENVIRONMENT=production
```

### 4. DEPLOY & MONITORING
- Railway automatycznie zbuduje z Dockerfile
- Bot uruchomi się automatycznie
- Scheduler zacznie o 6:00 codziennie

## 📊 AUTOMATYZACJA:
- **6:00 każdego dnia** → Zbieranie danych ze wszystkich pokojów
- **Raw data** → `raw_data/raw_raport_YYYY-MM-DD_room.json`
- **Quota monitoring** → Pełne logowanie wszystkich API calls

## 🔍 MONITORING:
- Railway Logs → Zobacz status bota
- Quota usage → Sprawdź w `quota_usage.json`
- Raw data → Nowe pliki codziennie

## ⚠️ WAŻNE:
- **Scheduler używa PRAWDZIWYCH API calls** (nie demo)
- **Spodziewany koszt:** ~300-500 quota dziennie
- **Raw data** → Podstawa dla komend `!name` i analiz 