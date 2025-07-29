# 🚨 EMERGENCY STARTUP GUIDE - HOOK BOOST WEB

## 🚨 Sytuacje awaryjne
- **Aplikacja nie odpowiada** po restarcie Railway
- **Volume został usunięty** lub uszkodzony
- **Błędne wdrożenie** - nowa wersja nie działa
- **Problemy z konfiguracją** - zmienne środowiskowe nie działają

## 🔧 SZYBKIE PRZYWRÓCENIE SYSTEMU

### Krok 1: Sprawdzenie statusu Railway
```bash
# Sprawdź czy aplikacja odpowiada
curl https://youtube-report-tool-production.up.railway.app/health

# Jeśli nie odpowiada, sprawdź logi
railway logs --tail 50
```

### Krok 2: Sprawdzenie volume
```bash
# Sprawdź czy volume istnieje
railway volume list

# Sprawdź dane w volume
railway volume inspect charismatic-volume
```

### Krok 3: Przywrócenie volume (jeśli uszkodzony)
```bash
# Jeśli volume nie istnieje, utwórz nowy
railway volume create charismatic-volume

# Podłącz volume do aplikacji
railway volume attach charismatic-volume
```

### Krok 4: Sprawdzenie zmiennych środowiskowych
```bash
# Sprawdź zmienne
railway variables

# Ustaw wymagane zmienne
railway variables set YOUTUBE_API_KEY=your_api_key_here
railway variables set RAILWAY_VOLUME_PATH=/mnt/volume
railway variables set RAILWAY_ENVIRONMENT=production
```

### Krok 5: Restart aplikacji
```bash
# Zrestartuj aplikację
railway service restart

# Sprawdź status
railway status
```

## 🔄 PEŁNE PRZYWRÓCENIE Z BACKUPU

### Krok 1: Pobranie backupu
```bash
# Pobierz najnowszy backup
wget https://github.com/michalpoznanski/youtube-report-tool/raw/main/backup/HOOK_BOOST_BACKUP_20250728_220704.zip

# Rozpakuj
unzip HOOK_BOOST_BACKUP_20250728_220704.zip -d hook-boost-restored/
cd hook-boost-restored/
```

### Krok 2: Przywrócenie na Railway
```bash
# Podłącz do projektu Railway
railway link

# Wdróż aplikację
railway up

# Sprawdź status
railway status
```

### Krok 3: Weryfikacja
```bash
# Sprawdź czy aplikacja odpowiada
curl https://youtube-report-tool-production.up.railway.app/health

# Sprawdź dane
curl https://youtube-report-tool-production.up.railway.app/api/v1/status
```

## 🛠️ MANUALNE PRZYWRÓCENIE DANYCH

### Jeśli volume jest uszkodzony, ale backup istnieje:

1. **Utwórz nowy volume:**
```bash
railway volume create charismatic-volume-new
```

2. **Podłącz volume:**
```bash
railway volume attach charismatic-volume-new
```

3. **Przywróć dane z backupu:**
```bash
# Rozpakuj backup
unzip HOOK_BOOST_BACKUP_20250728_220704.zip

# Skopiuj dane do volume
railway volume cp data/channels.json charismatic-volume-new:/mnt/volume/data/
railway volume cp data/quota_state.json charismatic-volume-new:/mnt/volume/data/
railway volume cp data/system_state.json charismatic-volume-new:/mnt/volume/data/
```

4. **Zrestartuj aplikację:**
```bash
railway service restart
```

## 🔍 DIAGNOSTYKA PROBLEMÓW

### Problem: Aplikacja nie uruchamia się
```bash
# Sprawdź logi
railway logs --tail 100

# Sprawdź zmienne środowiskowe
railway variables

# Sprawdź czy volume jest podłączony
railway volume list
```

### Problem: Dane nie są trwałe
```bash
# Sprawdź volume path
curl https://youtube-report-tool-production.up.railway.app/api/v1/debug/volume-config

# Sprawdź czy dane są w volume
railway volume inspect charismatic-volume
```

### Problem: Błędy API
```bash
# Sprawdź status aplikacji
curl https://youtube-report-tool-production.up.railway.app/health

# Sprawdź szczegółowe logi
railway logs --tail 100
```

## 📊 WERYFIKACJA SUKCESU

Po przywróceniu sprawdź:

1. **Status aplikacji:**
```bash
curl https://youtube-report-tool-production.up.railway.app/health
# Powinno zwrócić: {"status":"healthy","version":"1.0.0","scheduler_running":true}
```

2. **Dane kanałów:**
```bash
curl https://youtube-report-tool-production.up.railway.app/api/v1/channels
# Powinno zwrócić listę kanałów
```

3. **Kategorie:**
```bash
curl https://youtube-report-tool-production.up.railway.app/api/v1/categories
# Powinno zwrócić listę kategorii
```

4. **Status systemu:**
```bash
curl https://youtube-report-tool-production.up.railway.app/api/v1/status
# Powinno zwrócić pełny status systemu
```

## 🎯 AUTOMATYCZNE PRZYWRÓCENIE

### Skrypt automatycznego przywracania:
```bash
#!/bin/bash
# emergency_restore.sh

echo "🚨 Rozpoczynam automatyczne przywracanie Hook Boost Web..."

# 1. Sprawdź status
echo "📊 Sprawdzam status aplikacji..."
if curl -s https://youtube-report-tool-production.up.railway.app/health > /dev/null; then
    echo "✅ Aplikacja odpowiada"
else
    echo "❌ Aplikacja nie odpowiada - rozpoczynam przywracanie"
    
    # 2. Sprawdź volume
    echo "📁 Sprawdzam volume..."
    if railway volume list | grep -q "charismatic-volume"; then
        echo "✅ Volume istnieje"
    else
        echo "❌ Volume nie istnieje - tworzę nowy"
        railway volume create charismatic-volume
    fi
    
    # 3. Restart aplikacji
    echo "🔄 Restartuję aplikację..."
    railway service restart
    
    # 4. Czekaj na uruchomienie
    echo "⏳ Czekam na uruchomienie..."
    sleep 30
    
    # 5. Sprawdź ponownie
    if curl -s https://youtube-report-tool-production.up.railway.app/health > /dev/null; then
        echo "✅ Aplikacja przywrócona pomyślnie!"
    else
        echo "❌ Przywracanie nie powiodło się"
    fi
fi
```

## 📞 WSPARCIE AWARYJNE

W przypadku problemów:
1. **Sprawdź logi:** `railway logs --tail 100`
2. **Sprawdź volume:** `railway volume list`
3. **Sprawdź zmienne:** `railway variables`
4. **Skontaktuj się z administratorem**

---
**Ostatnia aktualizacja:** 2025-07-28 22:07:04  
**Wersja systemu:** Hook Boost Web v2.0  
**Backup:** HOOK_BOOST_BACKUP_20250728_220704.zip 