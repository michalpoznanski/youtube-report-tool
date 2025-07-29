# 🎯 Hook Boost Web - YouTube Analytics

Aplikacja webowa do raportowania danych z kanałów YouTube z interfejsem webowym i automatycznym schedulowaniem.

## 🚀 Funkcje

- **Interfejs webowy** do zarządzania kanałami YouTube
- **Automatyczne raporty** codziennie o 23:00
- **Generowanie plików CSV** z danymi z ostatnich 3 dni
- **Ekstrakcja nazwisk** z tytułów i opisów filmów
- **Kategoryzacja kanałów** (polityka, showbiz, sport, technologia)
- **Monitorowanie quota** YouTube API
- **REST API** do integracji z innymi systemami

## 📊 Struktura Raportów CSV

Każdy raport zawiera następujące kolumny:
- Channel_Name, Channel_ID
- Date_of_Publishing, Hour_GMT2
- Title, Description, Tags
- Video_Type (shorts vs long)
- View_Count, Like_Count, Comment_Count, Favorite_Count
- Definition, Has_Captions, Licensed_Content
- Topic_Categories, Names_Extracted
- Video_ID, Duration, Thumbnail_URL

## 🛠️ Instalacja

### Lokalnie

1. **Klonuj repozytorium:**
```bash
git clone <repository-url>
cd hook-boost-web
```

2. **Utwórz środowisko wirtualne:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

3. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

4. **Skonfiguruj zmienne środowiskowe:**
```bash
cp env.example .env
# Edytuj .env i dodaj swoje klucze API
```

5. **Uruchom aplikację:**
```bash
uvicorn app.main:app --reload
```

### Na Railway

1. **Przygotuj pliki:**
```bash
# Upewnij się, że masz wszystkie pliki:
# - Dockerfile
# - railway.json
# - requirements.txt
# - .env (z kluczami API)
```

2. **Deploy na Railway:**
```bash
# Zainstaluj Railway CLI
npm install -g @railway/cli

# Zaloguj się
railway login

# Deploy
railway up
```

3. **Skonfiguruj zmienne środowiskowe na Railway:**
```bash
railway variables set YOUTUBE_API_KEY=your_api_key
railway variables set SECRET_KEY=your_secret_key
```

## 🔧 Konfiguracja

### Zmienne środowiskowe

```env
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# FastAPI Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Scheduler Settings
SCHEDULER_HOUR=23
SCHEDULER_MINUTE=0
DAYS_BACK=3

# Storage Settings
DATA_DIR=data
REPORTS_DIR=reports
BACKUP_DIR=backups

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### YouTube API Key

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Włącz YouTube Data API v3
4. Utwórz klucz API w sekcji "Credentials"
5. Dodaj klucz do zmiennej `YOUTUBE_API_KEY`

## 📚 API Endpoints

### Kanały
- `POST /api/v1/channels` - Dodaj kanał
- `GET /api/v1/channels` - Lista kanałów
- `DELETE /api/v1/channels/{channel_id}` - Usuń kanał

### Raporty
- `POST /api/v1/reports/generate` - Generuj raport CSV
- `GET /api/v1/reports/list` - Lista dostępnych raportów
- `GET /api/v1/reports/download/{filename}` - Pobierz raport

### Status i Kontrola
- `GET /api/v1/status` - Status systemu
- `POST /api/v1/scheduler/start` - Uruchom scheduler
- `POST /api/v1/scheduler/stop` - Zatrzymaj scheduler

### Health Check
- `GET /health` - Sprawdź stan aplikacji

## 🧪 Testy

```bash
# Uruchom wszystkie testy
pytest

# Uruchom testy z pokryciem
pytest --cov=app

# Uruchom konkretny test
pytest tests/test_api.py::test_health_check
```

## 📁 Struktura Projektu

```
hook-boost-web/
├── app/
│   ├── api/              # Endpointy REST API
│   ├── youtube/          # Integracja z YouTube API
│   ├── analysis/         # Analiza danych, ekstrakcja nazwisk
│   ├── scheduler/        # Automatyczne zadania
│   ├── storage/          # Generowanie i zapis CSV
│   ├── config/           # Konfiguracja aplikacji
│   └── main.py           # Główna aplikacja FastAPI
├── templates/            # Szablony HTML
├── static/              # Pliki statyczne
├── tests/               # Testy
├── data/                # Dane aplikacji
├── reports/             # Wygenerowane raporty
├── logs/                # Logi aplikacji
├── Dockerfile           # Konfiguracja Docker
├── railway.json         # Konfiguracja Railway
├── requirements.txt     # Zależności Python
└── README.md           # Ten plik
```

## 🚀 Deployment

### Railway (Zalecane)

1. **Przygotuj repozytorium:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Deploy na Railway:**
```bash
railway init
railway up
```

3. **Skonfiguruj zmienne środowiskowe:**
```bash
railway variables set YOUTUBE_API_KEY=your_api_key
railway variables set SECRET_KEY=your_secret_key
```

### Docker

```bash
# Build image
docker build -t hook-boost-web .

# Run container
docker run -p 8000:8000 --env-file .env hook-boost-web
```

## 📊 Monitorowanie

### Logi
- Logi aplikacji: `logs/app.log`
- Poziom logowania: `LOG_LEVEL` w zmiennych środowiskowych

### Quota YouTube API
- Dzienny limit: 10,000 jednostek
- Monitorowanie w czasie rzeczywistym
- Reset codziennie o 23:00

### Status Schedulera
- Automatyczne raporty codziennie o 23:00
- Kontrola przez API endpoints
- Health checks co 5 minut

## 🔒 Bezpieczeństwo

- **Environment variables** - żadnych hardcodowanych kluczy
- **CORS** - konfigurowalne origins
- **Input validation** - sanityzacja wszystkich inputów
- **Rate limiting** - ochrona przed nadużyciami

## 🤝 Contributing

1. Fork repozytorium
2. Utwórz branch dla nowej funkcji
3. Commit zmiany
4. Push do branch
5. Utwórz Pull Request

## 📄 Licencja

MIT License

## 🆘 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Sprawdź status YouTube API
3. Sprawdź konfigurację zmiennych środowiskowych
4. Otwórz issue na GitHub

---

**Hook Boost Web** - Profesjonalne narzędzie do analizy kanałów YouTube! 🎯 