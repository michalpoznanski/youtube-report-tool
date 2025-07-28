# 🛡️ PRZEWODNIK BEZPIECZEŃSTWA HOOK BOOST

## ⚠️ KRYTYCZNE - PRZECZYTAJ NAJPIERW!

**TWOJE TOKENY BYŁY WYSTAWIONE PUBLICZNIE!** Ten przewodnik pomoże Ci zabezpieczyć kod.

---

## 🚨 NATYCHMIASTOWE DZIAŁANIA (WYKONAJ TERAZ!)

### 1. ZMIEŃ WSZYSTKIE TOKENY:

#### Discord Bot Token:
```
1. Idź do: https://discord.com/developers/applications
2. Wybierz swoją aplikację
3. Bot → Reset Token → Potwierdź
4. Skopiuj NOWY token (zapisz bezpiecznie!)
```

#### YouTube API Key:
```
1. Idź do: https://console.cloud.google.com/apis/credentials
2. Znajdź swój klucz API
3. Usuń stary klucz
4. Utwórz nowy klucz API
5. Skopiuj NOWY klucz
```

#### GitHub Personal Access Token:
```
1. Idź do: https://github.com/settings/tokens
2. Znajdź swój stary token
3. Usuń (Delete) ten token
4. Generate new token (classic)
5. Wybierz uprawnienia: repo, workflow
6. Skopiuj NOWY token
```

#### Railway Token:
```
1. Idź do: https://railway.app/account/tokens
2. Usuń istniejący token
3. Utwórz nowy token
4. Skopiuj NOWY token
```

---

## 🔧 KONFIGURACJA BEZPIECZEŃSTWA

### 1. Utwórz plik .env:
```bash
cp env.template .env
```

### 2. Uzułnij .env NOWYMI tokenami:
```bash
# Edytuj plik .env i wklej NOWE tokeny
nano .env
```

### 3. Sprawdź .gitignore:
```bash
# Upewnij się, że .env jest ignorowany
git status
# .env NIE POWINIEN być widoczny!
```

---

## 🐳 DOCKER SECRETS

### Dla produkcji użyj Docker secrets:

```dockerfile
# W Dockerfile dodaj:
RUN mkdir -p /run/secrets
```

### Runtime secrets:
```bash
# Przekaż tokeny jako zmienne środowiskowe
docker run -e DISCORD_TOKEN="new_token" your_image
```

---

## 🚀 DEPLOYMENT (Railway/Render)

### Railway:
```bash
# Ustaw zmienne środowiskowe w Railway Dashboard:
railway variables set DISCORD_TOKEN="new_discord_token"
railway variables set YOUTUBE_API_KEY="new_youtube_key"
```

### Render:
```bash
# W Render Dashboard → Environment:
DISCORD_TOKEN = new_discord_token
YOUTUBE_API_KEY = new_youtube_key
```

---

## ✅ SPRAWDZENIE BEZPIECZEŃSTWA

### Automatyczne sprawdzenie:
```python
python security_check.py
```

### Ręczne sprawdzenie:
```bash
# Sprawdź czy tokeny NIE są w kodzie:
grep -r "YOUR_OLD_TOKEN_PATTERN" . --exclude-dir=.git

# Wynik powinien być PUSTY!
```

---

## 📋 CHECKLIST BEZPIECZEŃSTWA

- [ ] ✅ Zmieniłem wszystkie tokeny (Discord, YouTube, GitHub, Railway)
- [ ] ✅ Utworzyłem plik .env z nowymi tokenami
- [ ] ✅ Sprawdziłem że .env jest w .gitignore
- [ ] ✅ Usunąłem hardcodowane tokeny z kodu
- [ ] ✅ Skonfigurałem deployment z nowymi tokenami
- [ ] ✅ Przetestowałem działanie z nowymi tokenami
- [ ] ✅ Przeprowadziłem security_check.py

---

## 🔐 NAJLEPSZE PRAKTYKI

### ✅ ROBIMY TAK:
```python
# Zawsze używaj zmiennych środowiskowych
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Sprawdzaj czy token istnieje
if not DISCORD_TOKEN:
    raise ValueError("Brak DISCORD_TOKEN")
```

### ❌ NIGDY TAK:
```python
# NIGDY nie wklejaj tokenów w kod!
DISCORD_TOKEN = "TWOJ_PRAWDZIWY_TOKEN"  # ❌ ZŁE!
```

### Więcej wskazówek:
- Używaj `.env` do developmentu
- Deployment = zmienne środowiskowe platformy
- Regularne rotowanie tokenów (co 3-6 miesięcy)
- Monitoruj logi pod kątem podejrzanej aktywności

---

## 📞 W RAZIE PROBLEMÓW

Jeśli masz problemy:
1. Sprawdź `.env` czy wszystkie tokeny są ustawione
2. Sprawdź logi: `docker logs container_name`
3. Sprawdź uprawnienia tokenów w dashboardach serwisów

---

**⚠️ PAMIĘTAJ: Bezpieczeństwo to proces, nie jednorazowa akcja!** 