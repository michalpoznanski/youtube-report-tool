FROM python:3.11-slim

WORKDIR /app

# Skopiuj requirements i zainstaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj kod aplikacji
COPY . .

# Utwórz foldery dla danych
RUN mkdir -p data/raw_data

# Uruchom bota
CMD ["python", "main.py"] 