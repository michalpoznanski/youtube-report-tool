# 🚀 HOOK BOOST V2 - YouTube Analytics Discord Bot

**Nowy bot z czystą architekturą i modularnym podejściem.**

## 📋 FILOZOFIA

- **Każdy pokój ma swoje kanały** - proste i logiczne
- **Bezpieczne quota** - oszczędne wykorzystanie API
- **Modularna architektura** - łatwa rozbudowa
- **Czyste komendy** - intuicyjne użycie

## 🎯 GŁÓWNE KOMENDY

| Komenda | Opis | Status |
|---------|------|--------|
| `!śledź` | Dodawanie kanałów do pokoju | ✅ GOTOWE |
| `!raport` | Zbieranie danych YouTube | 🚧 W BUDOWIE |
| `!name` | Analiza nazwisk | 🚧 W BUDOWIE |
| `!paliwo` | Status quota API | ✅ GOTOWE |

## 🔧 INSTALACJA I URUCHOMIENIE

### 1. Przygotowanie środowiska
```bash
# Ustaw zmienne środowiskowe
source config/env_setup.sh

# Sprawdź czy klucze są ustawione
echo $DISCORD_TOKEN
echo $YOUTUBE_API_KEY
```

### 2. Uruchomienie bota
```bash
python3 hook_boost_v2.py
```

### 3. Sprawdzenie statusu
```bash
# Na Discord użyj:
!status
!pomoc
```

## 📁 STRUKTURA PROJEKTU

```
BOT/
├── hook_boost_v2.py          # 🚀 Główny bot
├── sledz_system.py           # 📺 System śledzenia kanałów  
├── quota_manager.py          # ⛽ Zarządzanie quota
├── config/
│   ├── env_setup.sh         # 🔐 Konfiguracja środowiska
│   └── bot_settings.json    # ⚙️ Ustawienia bota
├── workshop/                # 🔬 Środowisko rozwoju
└── archive/                 # 📦 Archiwum starego bota
```

## 💾 MIGRACJA Z BOT V1

### ✅ CO ZOSTAŁO ZACHOWANE:
- 🔑 **Klucze API** - Discord Token, YouTube API Key
- ⛽ **QuotaManager** - system zarządzania quota
- 📊 **Integracje** - połączenia z API

### 🆕 CO ZOSTAŁO PRZEBUDOWANE:
- 🎯 **Architektura** - modularna, czysta
- 📺 **System kanałów** - pokoje zamiast kategorii
- 🚀 **Komendy** - uproszczone, intuicyjne

### 🗑️ CO ZOSTAŁO USUNIĘTE:
- 📁 **Stare kanały** - będą dodane na nowo
- 🏷️ **Kategorie** - zastąpione pokojami
- 🕸️ **Skomplikowany kod** - zastąpiony prostym

## 🎮 PRZYKŁADY UŻYCIA

### Dodawanie kanałów:
```
# Na pokoju #polityka
!śledź 
https://www.youtube.com/@TVP_INFO
https://www.youtube.com/watch?v=ABC123
https://youtu.be/XYZ789

# Bot automatycznie:
# 1. Wyciągnie Channel ID z linków
# 2. Doda kanały do pokoju #polityka  
# 3. Sprawdzi duplikaty
# 4. Pokaże podsumowanie
```

### Sprawdzanie quota:
```
!paliwo
# Wyświetli:
# - Dzisiejsze zużycie quota
# - Pozostały limit
# - Ostrzeżenia
```

## 🔐 BEZPIECZEŃSTWO

- **Klucze API** są w zmiennych środowiskowych
- **Backup** starego bota w `archive/`
- **Modularność** - łatwe testowanie
- **Quota safety** - kontrola zużycia API

## 🎯 ROADMAP

### Faza 1 (CURRENT): Podstawy ✅
- [x] Bot framework
- [x] System `!śledź`  
- [x] Quota manager
- [x] Dokumentacja

### Faza 2 (NEXT): Raporty 🚧
- [ ] System `!raport`
- [ ] CSV generation
- [ ] Date filtering
- [ ] API optimization

### Faza 3 (FUTURE): Analiza 🎯
- [ ] System `!name`
- [ ] Name normalization
- [ ] Statistics
- [ ] AI analysis

## 📞 POMOC

Jeśli masz problemy:

1. **Sprawdź zmienne środowiskowe**: `source config/env_setup.sh`
2. **Zobacz logi**: sprawdź komunikaty w terminalu
3. **Test status**: użyj `!status` na Discord
4. **Sprawdź quota**: użyj `!paliwo`

---

**🚀 HOOK BOOST V2 - Built with ❤️ in 2025** 