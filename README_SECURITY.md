# 🔒 Zabezpieczenia YouTube Analyzer Bot

## Problem
Bot miał tendencję do:
- Tworzenia wielu instancji
- Zawieszania się podczas operacji YouTube API
- Braku kontroli nad procesami

## Rozwiązania

### 1. 🔐 Kontrola pojedynczej instancji
- **Plik PID**: `bot.pid` - zapisuje ID procesu
- **Sprawdzanie na starcie**: Bot sprawdza czy już działa
- **Automatyczne czyszczenie**: Usuwa stary plik PID jeśli proces nie istnieje

### 2. ⏰ Timeout dla operacji API
- **YouTube API calls**: 30 sekund timeout
- **Video details**: 15 sekund timeout  
- **Analiza filmów**: 5 minut timeout
- **Zabezpieczenie przed zawieszaniem**: `asyncio.wait_for()`

### 3. 🛡️ Obsługa sygnałów
- **SIGINT** (Ctrl+C): Bezpieczne zamknięcie
- **SIGTERM**: Bezpieczne zamknięcie
- **Automatyczne czyszczenie**: Usuwa plik PID przy wyjściu

### 4. 🔧 Skrypty zarządzania

#### `start_bot.sh` - Uruchamianie bota
```bash
./start_bot.sh
```
- Sprawdza czy bot już działa
- Zabija stare procesy
- Uruchamia w tle z logami
- Sprawdza czy się uruchomił

#### `check_bot.py` - Zarządzanie procesami
```bash
python3 check_bot.py status    # Pokaż status
python3 check_bot.py kill      # Zabij wszystkie procesy  
python3 check_bot.py restart   # Restart bota
```

### 5. 📊 Monitoring
- **Logi**: `bot.log` - wszystkie logi bota
- **Status**: Sprawdzanie procesów w czasie rzeczywistym
- **PID tracking**: Śledzenie ID procesu

## Użycie

### Pierwsze uruchomienie
```bash
./start_bot.sh
```

### Sprawdzenie statusu
```bash
python3 check_bot.py status
```

### Restart bota
```bash
python3 check_bot.py restart
```

### Śledzenie logów
```bash
tail -f bot.log
```

### Zabicie wszystkich procesów
```bash
python3 check_bot.py kill
```

## Zabezpieczenia w kodzie

### 1. Kontrola PID na starcie
```python
def check_and_create_pid():
    if os.path.exists(PID_FILE):
        # Sprawdź czy proces działa
        if psutil.pid_exists(old_pid):
            print("❌ Bot już działa")
            sys.exit(1)
```

### 2. Timeout dla API
```python
channels_response = await asyncio.wait_for(
    asyncio.to_thread(self.youtube.channels().list(...).execute),
    timeout=30.0
)
```

### 3. Obsługa sygnałów
```python
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 4. Bezpieczne zamknięcie
```python
def cleanup_pid():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except:
        pass
```

## Korzyści

✅ **Jedna instancja**: Bot nigdy nie uruchomi się wielokrotnie  
✅ **Brak zawieszania**: Timeout zapobiega zawieszaniu się  
✅ **Łatwe zarządzanie**: Skrypty do kontroli procesów  
✅ **Bezpieczne zamknięcie**: Automatyczne czyszczenie przy wyjściu  
✅ **Monitoring**: Łatwe śledzenie statusu i logów  

## Troubleshooting

### Bot nie uruchamia się
```bash
python3 check_bot.py kill
./start_bot.sh
```

### Bot się zawiesza
```bash
python3 check_bot.py restart
```

### Sprawdzenie logów
```bash
tail -f bot.log
```

### Wymuszenie zabicia
```bash
pkill -f bot_yt_api.py
rm -f bot.pid
``` 