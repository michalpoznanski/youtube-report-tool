FROM python:3.11-slim

WORKDIR /app

# Install git for auto-commit
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create raw_data directory
RUN mkdir -p raw_data

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Start bot
CMD ["python", "main.py"]
