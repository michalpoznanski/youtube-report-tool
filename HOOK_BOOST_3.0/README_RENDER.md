# 🚀 HOOK BOOST 3.0 - Render.com Deployment

## 📋 Szybki Start

### 1. Konto Render.com
- Przejdź do [render.com](https://render.com)
- Zaloguj się przez GitHub
- Kliknij "New +" → "Web Service"

### 2. Połącz z GitHub
- Wybierz repozytorium `michalpoznanski/hookboost`
- Render automatycznie wykryje `render.yaml`

### 3. Konfiguracja
- **Name**: `hook-boost-3-0`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

### 4. Zmienne Środowiskowe
Dodaj w sekcji "Environment Variables":
```
DISCORD_TOKEN = [twój_nowy_token_discord]
YOUTUBE_API_KEY = [twój_klucz_youtube_api]
GITHUB_TOKEN = [twój_token_github]
```

### 5. Deploy
- Kliknij "Create Web Service"
- Render automatycznie zbuduje i uruchomi bota

## 🔄 Automatyczny Deployment
- Każdy push do `main` branch = automatyczny restart
- Render wykrywa zmiany w GitHub
- Bot restartuje się z nowym kodem

## 📊 Logi
- W Render Dashboard → Logs
- Real-time logi z bota
- Łatwe debugowanie

## 💰 Koszt
- **Darmowy tier**: 750h/miesiąc
- Wystarczy dla 24/7 bota
- Brak ukrytych kosztów 