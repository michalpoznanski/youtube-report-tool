#!/usr/bin/env python3
"""
INICJALIZACJA PUSTEGO GITHUB REPO
=================================

Dodaje pierwsze pliki do pustego repo hookboost
"""

import requests
import base64
import json

# GitHub token
# 🛡️ BEZPIECZEŃSTWO: Token usunięty!
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("❌ Brak GITHUB_TOKEN w zmiennych środowiskowych!")

# Headers dla GitHub API
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def create_file_in_repo(file_path, content, message):
    """Tworzy plik w repo przez GitHub API"""
    
    url = f"https://api.github.com/repos/michalpozanski/hookboost/contents/{file_path}"
    
    data = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode()
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Utworzono: {file_path}")
        return True
    else:
        print(f"❌ Błąd {file_path}: {response.status_code} - {response.text}")
        return False

def init_repo():
    """Inicjalizuje repo pierwszymi plikami"""
    
    print("🚀 INICJALIZACJA PUSTEGO REPO")
    print("=" * 40)
    
    # Podstawowe pliki do inicjalizacji
    files = {
        "README.md": """# Hook Boost Bot

Discord bot for YouTube channel tracking and analysis.

## Features
- Channel tracking (!śledź)
- Daily reports (!raport) 
- Name analysis (!name)
- Railway deployment

## Setup
1. Configure environment variables
2. Deploy to Railway
3. Use Discord commands

## Commands
- `!śledź` - Track YouTube channels
- `!raport` - Generate daily reports
- `!name` - Analyze trending names
- `!sync` - Railway sync utilities
""",
        
        "main.py": """#!/usr/bin/env python3
\"\"\"
HOOK BOOST V2 - DISCORD BOT
==========================

Main bot file for Railway deployment
\"\"\"

import discord
from discord.ext import commands
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot zalogowany jako {bot.user}')
    print(f'🏠 Serwery: {len(bot.guilds)}')

@bot.command(name='pomoc')
async def help_command(ctx):
    embed = discord.Embed(
        title="🤖 Hook Boost - Pomoc",
        description="Dostępne komendy:",
        color=0x00ff00
    )
    embed.add_field(name="!śledź", value="Dodaj kanały YouTube do śledzenia", inline=False)
    embed.add_field(name="!raport", value="Wygeneruj raport dzienny", inline=False)
    embed.add_field(name="!name", value="Analizuj trendy nazwisk", inline=False)
    embed.add_field(name="!sync", value="Narzędzia synchronizacji Railway", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status_command(ctx):
    embed = discord.Embed(
        title="📊 Status Bota",
        description="Hook Boost działa poprawnie!",
        color=0x00ff00
    )
    embed.add_field(name="Serwery", value=len(bot.guilds), inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await ctx.send(embed=embed)

# Run bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ Brak DISCORD_TOKEN w zmiennych środowiskowych")
""",
        
        "requirements.txt": """discord.py==2.3.2
google-api-python-client==2.108.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
schedule==1.2.0
""",
        
        "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p raw_data config

CMD ["python3", "main.py"]
""",
        
        "railway.json": """{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "restartPolicyType": "ALWAYS",
    "sleepApplication": false
  },
  "environments": {
    "production": {
      "variables": {
        "RAILWAY_ENVIRONMENT": "production"
      }
    }
  }
}
"""
    }
    
    success_count = 0
    total_files = len(files)
    
    for file_path, content in files.items():
        if create_file_in_repo(file_path, content, f"Initial commit: {file_path}"):
            success_count += 1
    
    print(f"\n📊 WYNIKI INICJALIZACJI:")
    print(f"✅ Utworzono: {success_count}/{total_files} plików")
    
    if success_count == total_files:
        print("🎉 REPO ZAINICJALIZOWANE POMYŚLNIE!")
        print("🚀 Możesz teraz używać Railway Sync V2")
    else:
        print("⚠️ NIEKTÓRE PLIKI NIE ZOSTAŁY UTWORZONE")

if __name__ == "__main__":
    init_repo() 