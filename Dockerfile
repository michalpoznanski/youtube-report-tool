# 🚀 HOOK BOOST V2 - ULTRA LEAN DOCKERFILE
# =======================================
# Minimal Docker image for Railway deployment

# Cache buster 1

FROM python:3.11-slim

# Ustaw zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# Uruchom aplikację
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"] 

# Cache buster 2 - FORCE REBUILD 

# Cache buster 3 - FINAL FORCE REBUILD 

# Cache buster 4 - FORCE TEMPLATES UPDATE
# Cache buster 5 - FORCE CSV PROCESSOR UPDATE 