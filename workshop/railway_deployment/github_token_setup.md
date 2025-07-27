# GITHUB PERSONAL ACCESS TOKEN - SETUP
====================================

## KROK 1: WYGENERUJ TOKEN
1. Idź do: https://github.com/settings/tokens
2. Kliknij "Generate new token (classic)"
3. Ustaw:
   - Note: `Hook Boost Railway Sync`
   - Expiration: `90 days`
   - Scopes: ✅ `repo` (pełny dostęp)
4. Kliknij "Generate token"
5. **SKOPIUJ TOKEN** (będzie widoczny tylko raz!)

## KROK 2: UŻYJ TOKENU W KODZIE

```python
from railway_sync_v2 import RailwaySyncV2

# Twój token (zastąp xxxxxx swoim tokenem)
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"

# Inicjalizuj z tokenem
sync = RailwaySyncV2(github_token=GITHUB_TOKEN)

# Setup git repo (bez pytania o hasło)
sync.setup_local_git()

# Automatyczna synchronizacja
sync.sync_to_railway_auto("Dodaję nową funkcję !raport")
```

## KROK 3: BEZPIECZNE PRZECHOWYWANIE

### OPCJA A: Zmienna środowiskowa
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

### OPCJA B: Plik .env (zalecane)
```bash
# Stwórz plik .env w folderze workshop/railway_deployment/
echo "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx" > .env
```

### OPCJA C: W kodzie (tymczasowo)
```python
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"  # Tylko do testów!
```

## KROK 4: TEST TOKENU

```python
# Test czy token działa
sync = RailwaySyncV2(github_token=GITHUB_TOKEN)
if sync.setup_local_git():
    print("✅ Token działa!")
else:
    print("❌ Problem z tokenem")
```

## WAŻNE:
- 🔒 **NIGDY nie commit tokenu do Git!**
- 🔄 **Token wygasa po 90 dniach**
- 📝 **Zapisz token w bezpiecznym miejscu**
- 🚫 **Nie udostępniaj tokenu nikomu**

## PRZYKŁADY UŻYCIA:

```python
# Pełna automatyczna sync
sync.sync_to_railway_auto("Update main.py with new features")

# Szybka sync jednego pliku
sync.quick_sync("main.py", "Fix bug in !raport")

# Sync tylko kodu
sync.sync_code_only()

# Sync tylko config
sync.sync_config_only()
``` 