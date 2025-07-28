FROM python:3.11-slim-buster

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 🛡️ BEZPIECZEŃSTWO: Utwórz katalogi dla sekretów
RUN mkdir -p /run/secrets && \
    chmod 700 /run/secrets

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/raw_data

# Set permissions
RUN chmod -R 755 data/

# 🛡️ BEZPIECZEŃSTWO: Nie eksponuj portów bez potrzeby
# EXPOSE 8000

# 🛡️ BEZPIECZEŃSTWO: Sprawdź obecność zmiennych środowiskowych
RUN echo '#!/bin/bash\n\
if [ -z "$DISCORD_TOKEN" ] || [ -z "$YOUTUBE_API_KEY" ]; then\n\
    echo "❌ BŁĄD: Brak wymaganych zmiennych środowiskowych!"\n\
    echo "   Wymagane: DISCORD_TOKEN, YOUTUBE_API_KEY"\n\
    exit 1\n\
fi\n\
exec python main.py "$@"' > /app/secure_start.sh && \
    chmod +x /app/secure_start.sh

# 🔒 Uruchom z bezpiecznym sprawdzeniem
CMD ["/app/secure_start.sh"] 