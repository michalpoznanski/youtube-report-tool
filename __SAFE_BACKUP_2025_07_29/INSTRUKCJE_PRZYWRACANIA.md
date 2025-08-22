# 🔄 INSTRUKCJE PRZYWRACANIA SYSTEMU

## 🎯 **SPOSÓB 1: Z BACKUPU LOKALNEGO**

### Krok 1: Skopiuj backup
```bash
cp -r /Users/maczek/Desktop/BOT/backup/HOOK_BOOST_WEB_WORKING_20250728_170851/hook-boost-web /nowa/lokalizacja/
```

### Krok 2: Przejdź do katalogu
```bash
cd /nowa/lokalizacja/hook-boost-web
```

### Krok 3: Skonfiguruj zmienne środowiskowe
```bash
cp env.example .env
# Edytuj .env i ustaw:
# YOUTUBE_API_KEY=twój_klucz_api
# SECRET_KEY=twój_secret_key
```

### Krok 4: Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### Krok 5: Uruchom aplikację
```bash
python run.py
```

## 🎯 **SPOSÓB 2: Z GITHUB**

### Krok 1: Sklonuj repozytorium
```bash
git clone https://github.com/michalpoznanski/youtube-report-tool.git
cd youtube-report-tool
```

### Krok 2: Przejdź do działającego commita
```bash
git checkout a51c166
```

### Krok 3: Skonfiguruj zmienne środowiskowe
```bash
cp env.example .env
# Edytuj .env
```

### Krok 4: Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### Krok 5: Uruchom aplikację
```bash
python run.py
```

## 🚀 **DEPLOYMENT NA RAILWAY**

### Krok 1: Połącz z Railway
```bash
railway login
railway init
```

### Krok 2: Ustaw zmienne środowiskowe
```bash
railway variables set YOUTUBE_API_KEY=twój_klucz_api
railway variables set SECRET_KEY=twój_secret_key
```

### Krok 3: Deploy
```bash
railway up
```

## ✅ **TESTY PO PRZYWRÓCENIU**

1. **Sprawdź healthcheck:** `curl http://localhost:8000/health`
2. **Dodaj kanał:** `https://www.youtube.com/@SuperExpressOfficial`
3. **Wygeneruj raport:** Sprawdź czy działa
4. **Sprawdź scheduler:** Status powinien być "running"

## 🎯 **WAŻNE INFORMACJE**

- **Ostatni działający commit:** `a51c166`
- **Data backupu:** 28.07.2025, 17:08:51
- **Status:** ✅ Pełni funkcjonalny system
- **Wszystkie błędy naprawione:** ✅

---

**🎉 SYSTEM JEST GOTOWY DO UŻYCIA PO PRZYWRÓCENIU!** 