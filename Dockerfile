# 🚀 HOOK BOOST V2 - ULTRA LEAN DOCKERFILE
# =======================================
# Minimal Docker image for Railway deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install git for auto-commit functionality
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create raw_data directory for CSV outputs
RUN mkdir -p raw_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port (Railway requirement)
EXPOSE 8080

# Start the Discord bot
CMD ["python", "main.py"] 