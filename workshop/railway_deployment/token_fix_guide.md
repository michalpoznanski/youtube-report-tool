# NAPRAWA GITHUB TOKEN - UPRAWNIENIA
====================================

## PROBLEM:
Token nie ma uprawnień do zapisu w repo.

## ROZWIĄZANIE:

### 1. IDŹ DO GITHUB SETTINGS:
```
https://github.com/settings/tokens
```

### 2. USUŃ STARY TOKEN:
- Znajdź token "Hook Boost Railway Sync"
- Kliknij "Delete"
- Potwierdź usunięcie

### 3. WYGENERUJ NOWY TOKEN:
- Kliknij "Generate new token (classic)"
- **Note:** `Hook Boost Railway Sync V2`
- **Expiration:** `90 days`
- **Scopes:** ✅ `repo` (PEŁNY DOSTĘP DO REPO)

### 4. WAŻNE UPRAWNIENIA:
```
✅ repo (Full control of private repositories)
   ├── repo:status
   ├── repo_deployment
   ├── public_repo
   ├── repo:invite
   └── security_events
```

### 5. SKOPIUJ NOWY TOKEN I ZASTĄP W KODZIE:

```python
# W railway_sync_v2.py i init_repo.py
GITHUB_TOKEN = "ghp_NOWY_TOKEN_TUTAJ"
```

### 6. PRZETESTUJ:
```bash
python3 init_repo.py
```

## ALTERNATYWNE ROZWIĄZANIE:

### RĘCZNE DODANIE PLIKÓW:
1. Idź do: https://github.com/michalpoznanski/hookboost
2. Kliknij "Add file" → "Create new file"
3. Nazwa: `README.md`
4. Treść:
```markdown
# Hook Boost Bot

Discord bot for YouTube channel tracking and analysis.

## Features
- Channel tracking (!śledź)
- Daily reports (!raport) 
- Name analysis (!name)
- Railway deployment
```
5. Kliknij "Commit new file"

### PO DODANIU PIERWSZEGO PLIKU:
- Railway Sync V2 powinien działać
- Git clone będzie możliwy
- Automatyczna synchronizacja zadziała 