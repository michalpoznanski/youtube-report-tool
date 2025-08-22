#!/bin/bash
# 🔐 KONFIGURACJA ŚRODOWISKA - BOT V2
# Automatyczne ustawienie zmiennych środowiskowych

echo "🚀 Ustawiam środowisko dla Bot V2..."

# Discord Bot Token
# 🛡️ BEZPIECZEŃSTWO: Użyj pliku .env zamiast hardcodowania!
# export DISCORD_TOKEN="USUŃ_STARY_TOKEN_I_UŻYJ_.ENV" 
echo "⚠️  UWAGA: Ten plik zawierał hardcodowane tokeny!"
echo "📝 Użyj pliku .env do przechowywania tokenów"
echo "💡 Zobacz: SECURITY_SETUP.md"

# YouTube Data API v3 Key  
# 🛡️ BEZPIECZEŃSTWO: Użyj pliku .env zamiast hardcodowania!
# export YOUTUBE_API_KEY="USUŃ_STARY_TOKEN_I_UŻYJ_.ENV"

echo "✅ Zmienne środowiskowe ustawione:"
echo "   DISCORD_TOKEN: ${DISCORD_TOKEN:0:20}..."
echo "   YOUTUBE_API_KEY: ${YOUTUBE_API_KEY:0:20}..."
echo ""
echo "🎯 Gotowy do uruchomienia Bot V2!"
echo "   Użyj: python3 bot_v2.py" 