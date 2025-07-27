#!/bin/bash
# 🔐 KONFIGURACJA ŚRODOWISKA - BOT V2
# Automatyczne ustawienie zmiennych środowiskowych

echo "🚀 Ustawiam środowisko dla Bot V2..."

# Discord Bot Token
export DISCORD_TOKEN="MTM5NTcyNzA3OTE1MjAyOTc2Ng.GiIrWA.K8UgzKgCMut7m1-uONE3dPGBRNwBBAqRecSkZ8"

# YouTube Data API v3 Key  
export YOUTUBE_API_KEY="AIzaSyCpWQ8QXUIXEy3hOda2Wa0UAUFIq-Ivm30"

echo "✅ Zmienne środowiskowe ustawione:"
echo "   DISCORD_TOKEN: ${DISCORD_TOKEN:0:20}..."
echo "   YOUTUBE_API_KEY: ${YOUTUBE_API_KEY:0:20}..."
echo ""
echo "🎯 Gotowy do uruchomienia Bot V2!"
echo "   Użyj: python3 bot_v2.py" 