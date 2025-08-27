# 🚀 HOOK BOOST V2 - ULTRA LEAN DOCKERFILE
# =======================================
# Minimal Docker image for Railway deployment

# Cache buster 1

FROM python:3.11-slim

# Ustaw zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENABLE_TREND=true

# Ustaw katalog roboczy
WORKDIR /app

# Zainstaluj zależności systemowe
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Skopiuj plik requirements i zainstaluj zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj kod aplikacji
COPY . .

# Utwórz katalogi dla danych
RUN mkdir -p data reports backups logs

# Ustaw uprawnienia
RUN chmod +x /app/start.sh

# Eksponuj port
EXPOSE 8000

# Uruchom aplikację przez run.py (zgodnie z Railway)
CMD ["python", "run.py"]

# Cache buster 2 - FORCE REBUILD 

# Cache buster 3 - FINAL FORCE REBUILD 

# Cache buster 4 - FORCE TEMPLATES UPDATE
# Cache buster 5 - FORCE CSV PROCESSOR UPDATE
# Cache buster 6 - FORCE TREND ANALYSIS UPDATE
# Cache buster 7 - FORCE FULL REDEPLOYMENT - TREND ENDPOINTS
# Cache buster 8 - FORCE TREND MODULE ENABLE
# Cache buster 9 - FORCE TREND ROUTING FIX 