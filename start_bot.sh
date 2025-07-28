#!/bin/bash

# Skrypt do uruchamiania bota YouTube Analyzer z zabezpieczeniami

echo "🤖 YouTube Analyzer Bot - Starter"
echo "=================================="

# Sprawdź czy bot już działa
if [ -f "bot.pid" ]; then
    OLD_PID=$(cat bot.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "❌ Bot już działa (PID: $OLD_PID)"
        echo "Użyj: python3 check_bot.py kill"
        exit 1
    else
        echo "⚠️ Znaleziono stary plik PID, ale proces nie działa"
        rm -f bot.pid
    fi
fi

# Sprawdź czy są inne procesy bota
BOT_PROCESSES=$(pgrep -f "bot_yt_api.py" | wc -l)
if [ $BOT_PROCESSES -gt 0 ]; then
    echo "❌ Znaleziono $BOT_PROCESSES uruchomionych procesów bota"
    echo "Zabijam wszystkie procesy..."
    pkill -f "bot_yt_api.py"
    sleep 2
fi

# Sprawdź czy pliki istnieją
if [ ! -f "bot_yt_api.py" ]; then
    echo "❌ Plik bot_yt_api.py nie istnieje"
    exit 1
fi

# Ustaw zmienne środowiskowe
# 🛡️ BEZPIECZEŃSTWO: Użyj pliku .env zamiast hardcodowania!
# export DISCORD_TOKEN="USUŃ_STARY_TOKEN_I_UŻYJ_.ENV"
source .env  # Ładuj z bezpiecznego pliku .env
# 🛡️ BEZPIECZEŃSTWO: Użyj pliku .env zamiast hardcodowania!
# export YOUTUBE_API_KEY="USUŃ_STARY_TOKEN_I_UŻYJ_.ENV"

echo "🚀 Uruchamiam bota w tle..."

# Uruchom bota w tle
nohup python3 bot_yt_api.py > bot.log 2>&1 &
BOT_PID=$!

# Zapisz PID
echo $BOT_PID > bot.pid

echo "✅ Bot uruchomiony (PID: $BOT_PID)"
echo "📄 Logi: bot.log"
echo "📄 PID: bot.pid"

# Sprawdź czy bot się uruchomił
sleep 3
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "🟢 Bot działa poprawnie"
else
    echo "🔴 Bot nie uruchomił się poprawnie"
    echo "Sprawdź logi: tail -f bot.log"
    exit 1
fi

echo ""
echo "📋 Przydatne komendy:"
echo "  tail -f bot.log          - Śledź logi na żywo"
echo "  python3 check_bot.py status  - Sprawdź status"
echo "  python3 check_bot.py kill    - Zabij bota"
echo "  python3 check_bot.py restart - Restart bota" 