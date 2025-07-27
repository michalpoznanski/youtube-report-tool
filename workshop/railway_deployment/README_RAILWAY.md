# RAILWAY.APP DEPLOYMENT - HOOK BOOST

## 📋 CHECKLIST PRZYGOTOWANIA:

### 1. KONTO RAILWAY
- [ ] Załóż konto na https://railway.app
- [ ] Połącz z GitHub
- [ ] Verify email

### 2. STRUKTURA PROJEKTU
```
hook_boost_railway/
├── main.py                    # Bot Discord
├── scheduler.py               # Cron jobs (codzienne raporty)
├── Dockerfile                 # Railway container
├── requirements.txt           # Dependencies
├── railway.json               # Railway config
├── modules/
│   ├── sledz_system.py        # !śledź
│   ├── raport_system.py       # !raport
│   └── name_system.py         # !name
├── raw_data/                  # Persistent storage
└── config/
    ├── channels_config.json
    └── quota_usage.json
```

### 3. ENVIRONMENT VARIABLES (Railway)
```
DISCORD_TOKEN=your_discord_token
YOUTUBE_API_KEY=your_youtube_key
RAILWAY_ENVIRONMENT=production
```

### 4. RAILWAY FEATURES
- ✅ 500h/miesiąc DARMOWO
- ✅ Persistent volumes dla raw_data/
- ✅ Automatic deploys z GitHub
- ✅ Cron jobs
- ✅ Logs monitoring

## 🚀 DEPLOYMENT STEPS:
1. Przygotować kod w warsztacie
2. Push do GitHub repo
3. Connect Railway → GitHub
4. Configure environment vars
5. Deploy & test

## 💾 BACKUP STRATEGY:
- Codzienne raporty → `raw_data/`
- Cotygodniowy backup → GitHub
- Quota logs → persistent storage 