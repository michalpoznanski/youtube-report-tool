#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 HOOK BOOST V3 - ULTRA LEAN
=============================

Discord bot do monitorowania kanałów YouTube i generowania surowych danych.
Ultra-lekki, modularny, zero analizy - tylko surowe dane.

AUTOR: Hook Boost V3 - Ultra Lean Edition
WERSJA: 3.0 (Clean Architecture)
"""

import os
import sys
import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

# Dodaj ścieżkę do modułów
sys.path.append('modules')

from modules.discord_bot import DiscordBot
from modules.config_manager import ConfigManager

# ===== KONFIGURACJA =====

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not DISCORD_TOKEN or not YOUTUBE_API_KEY:
    print("❌ Brak wymaganych zmiennych środowiskowych:")
    print("   - DISCORD_TOKEN")
    print("   - YOUTUBE_API_KEY")
    sys.exit(1)

# ===== INICJALIZACJA =====

def main():
    """Główna funkcja uruchamiająca bota"""
    print("🚀 HOOK BOOST V3 - ULTRA LEAN")
    print("   Discord bot do surowych danych YouTube")
    print("   Zero analizy - tylko CSV generation")
    print("=" * 50)
    
    # Inicjalizuj konfigurację
    config = ConfigManager()
    config.ensure_directories()
    
    # Inicjalizuj bota Discord
    bot = DiscordBot(
        discord_token=DISCORD_TOKEN,
        youtube_api_key=YOUTUBE_API_KEY,
        config_manager=config
    )
    
    # Uruchom bota
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot zatrzymany przez użytkownika")
    except Exception as e:
        print(f"❌ Błąd uruchomienia bota: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 