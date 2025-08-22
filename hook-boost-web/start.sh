#!/bin/bash

echo "🚀 Uruchamianie Hook Boost Web..."

# Sprawdź czy zmienne środowiskowe są ustawione
if [ -z "$YOUTUBE_API_KEY" ]; then
    echo "❌ BŁĄD: Brak zmiennej YOUTUBE_API_KEY!"
    echo "   Ustaw zmienną środowiskową YOUTUBE_API_KEY"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ BŁĄD: Brak zmiennej SECRET_KEY!"
    echo "   Ustaw zmienną środowiskową SECRET_KEY"
    exit 1
fi

echo "✅ Zmienne środowiskowe sprawdzone"
echo "📊 YouTube API Key: ${YOUTUBE_API_KEY:0:10}..."
echo "🔐 Secret Key: ${SECRET_KEY:0:10}..."

# Uruchom aplikację
echo "🌐 Uruchamianie serwera na porcie ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 