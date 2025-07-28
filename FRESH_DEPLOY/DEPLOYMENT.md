# 🚀 HOOK BOOST 3.0 - DEPLOYMENT GUIDE

## 📋 WYMAGANIA

### Zmienne środowiskowe (Railway):
```
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
GITHUB_TOKEN=your_github_personal_access_token (opcjonalne)
```

## 🔧 KROKI DEPLOYMENTU

### 1. GitHub Repository
1. Utwórz nowe repozytorium na GitHub
2. Wgraj pliki Hook Boost 3.0
3. Ustaw GITHUB_TOKEN (opcjonalne)

### 2. Railway Deployment
1. Połącz Railway z GitHub repository
2. Ustaw zmienne środowiskowe
3. Deploy automatyczny

### 3. Discord Bot
1. Utwórz aplikację Discord
2. Dodaj bot do serwera
3. Skopiuj token do Railway

## 📊 STRUKTURA PROJEKTU

```
HOOK_BOOST_3.0/
├── main.py                    # Bot Discord
├── modules/                   # Moduły systemu
├── data/                      # Dane i konfiguracja
├── Dockerfile                 # Railway container
├── railway.json              # Railway config
├── requirements.txt          # Python dependencies
└── README.md                 # Dokumentacja
```

## 🎯 FUNKCJONALNOŚCI

### Komendy Discord:
- `!śledź` - dodawanie kanałów YouTube
- `!raport` - generowanie 17-kolumnowego CSV
- `!scheduler` - status automatycznych raportów
- `!git` - status GitHub integration
- `!status` - status systemu

### Automatyzacja:
- Codzienne raporty o 6:00 UTC
- Auto-commit do GitHub
- Ultra lean mode (bez QuotaManager)

## ⚙️ KONFIGURACJA

### Railway Environment Variables:
1. `DISCORD_TOKEN` - token bota Discord
2. `YOUTUBE_API_KEY` - klucz YouTube Data API v3
3. `GITHUB_TOKEN` - token GitHub (auto-commit)

### Discord Bot Permissions:
- Send Messages
- Read Message History
- Use Slash Commands

## 🔗 LINKI

- **GitHub:** https://github.com/michalpoznanski/hookboost
- **Railway:** https://railway.app
- **Discord Developer Portal:** https://discord.com/developers/applications

---

**🚀 HOOK BOOST 3.0 - Ready for deployment!** 