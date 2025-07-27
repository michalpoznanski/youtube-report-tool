#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 HOOK BOOST 3.0 - ULTRA LEAN
==============================

Discord bot do monitorowania kanałów YouTube i generowania surowych danych.
Ultra-lekki, modularny, zero analizy - tylko surowe dane.

AUTOR: Hook Boost 3.0 - Ultra Lean Edition
WERSJA: 3.0 (Clean Architecture)
"""

import os
import sys
import traceback
import time
import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Dodaj ścieżkę do modułów
sys.path.append('modules')

from modules.sledz_system import SledzSystem
from modules.raport_system import RaportSystem
from modules.config_manager import ConfigManager
from modules.scheduler import AutoScheduler
from modules.git_manager import GitManager

# ===== KONFIGURACJA =====

print("🔍 DIAGNOSTYKA RAILWAY:")
print(f"📁 Katalog roboczy: {os.getcwd()}")
print(f"📁 Zawartość katalogu: {os.listdir('.')}")

# Test Git
import subprocess
try:
    git_version = subprocess.run(['git', '--version'], capture_output=True, text=True)
    print(f"🔧 Git: {git_version.stdout.strip() if git_version.returncode == 0 else '❌ BRAK'}")
except Exception as e:
    print(f"🔧 Git: ❌ BŁĄD - {e}")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

print(f"🔧 DISCORD_TOKEN: {'✅ Ustawiony' if DISCORD_TOKEN else '❌ BRAK'}")
print(f"🔧 YOUTUBE_API_KEY: {'✅ Ustawiony' if YOUTUBE_API_KEY else '❌ BRAK'}")
print(f"🔧 GITHUB_TOKEN: {'✅ Ustawiony' if GITHUB_TOKEN else '❌ BRAK'}")

if not DISCORD_TOKEN or not YOUTUBE_API_KEY:
    print("❌ Brak wymaganych zmiennych środowiskowych:")
    print("   - DISCORD_TOKEN")
    print("   - YOUTUBE_API_KEY")
    print("🔄 Próba uruchomienia w trybie demo...")
    # Nie wyłączamy aplikacji - pozwalamy jej działać
    DISCORD_TOKEN = "DEMO_TOKEN"
    YOUTUBE_API_KEY = "DEMO_KEY"

# ===== DISCORD BOT SETUP =====

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== INICJALIZACJA SYSTEMÓW =====

try:
    config_manager = ConfigManager()
    sledz_system = SledzSystem(api_key=YOUTUBE_API_KEY)
    raport_system = RaportSystem(api_key=YOUTUBE_API_KEY)
    scheduler = AutoScheduler()
    git_manager = GitManager()
    print("✅ Wszystkie systemy zainicjalizowane")
except Exception as e:
    print(f"⚠️ Błąd inicjalizacji systemów: {e}")
    print("🔄 Kontynuowanie z ograniczoną funkcjonalnością...")

print("🚀 HOOK BOOST 3.0 - ULTRA LEAN")
print("   Discord bot do surowych danych YouTube")
print("   Zero analizy - tylko CSV generation")
print("=" * 50)

# ===== EVENTS =====

@bot.event
async def on_ready():
    """Bot gotowy"""
    print(f"✅ {bot.user} jest gotowy!")
    print(f"📺 Serwery: {len(bot.guilds)}")
    
    total_members = sum(guild.member_count or 0 for guild in bot.guilds)
    print(f"👥 Użytkownicy: {total_members}")
    
    activity = discord.Activity(
        type=discord.ActivityType.watching, 
        name="!raport | Hook Boost 3.0"
    )
    await bot.change_presence(activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """Obsługa błędów"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Nieznana komenda!** Użyj `!pomoc`")
    else:
        await ctx.send(f"❌ **Błąd:** {str(error)}")
        print(f"Błąd komendy: {error}")

# ===== KOMENDY =====

@bot.command(name="pomoc", aliases=["h"])
async def help_command(ctx):
    """Pokazuje listę dostępnych komend"""
    embed = discord.Embed(
        title="🚀 **HOOK BOOST 3.0** - Ultra Lean",
        description="Bot do zbierania surowych danych YouTube (17-kolumnowy CSV)",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="📺 **Zarządzanie kanałami**",
        value="`!śledź [linki]` - Dodaje kanały do tego pokoju\n"
              "`!raport` - Generuje 17-kolumnowy CSV",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ **Informacje**",
        value="`!status` - Status systemu\n"
              "`!scheduler` - Status automatycznych raportów\n"
              "`!git` - Status GitHub\n"
              "`!pomoc` lub `!h` - Ta wiadomość",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **Ultra Lean Philosophy**",
        value="• Multi-room (każdy pokój = kategoria)\n"
              "• Surowe dane bez analizy\n"
              "• 17 kolumn CSV\n"
              "• Auto-commit GitHub",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="status")
async def status_command(ctx):
    """Status Hook Boost 3.0"""
    import uuid
    response_id = str(uuid.uuid4())[:8]  # Unikalny ID
    
    embed = discord.Embed(
        title=f"🤖 **Hook Boost 3.0 Status** [ID: {response_id}]",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="🚀 **Wersja**",
        value="```\nHook Boost 3.0 - Ultra Lean\nWersja: 3.0\nKod: Nowy od podstaw\n```",
        inline=False
    )
    
    # Sprawdź kanały w pokoju
    room_name = ctx.channel.name
    channels = sledz_system.get_room_channels(room_name)
    
    embed.add_field(
        name="📺 **Kanały**",
        value=f"```\nPokój: #{room_name}\nKanały: {len(channels)}\n```",
        inline=False
    )
    
    embed.add_field(
        name="⚡ **Ultra Lean**",
        value="```\nQuota Manager: DISABLED\nAnaliza: OFFLINE\nFormat: 17-kolumn CSV\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="śledź")
async def sledz_command(ctx, *, message: str = None):
    """Dodaj kanały YouTube do śledzenia"""
    try:
        if not message:
            # Sprawdź poprzednią wiadomość
            async for msg in ctx.channel.history(limit=2):
                if msg.author == ctx.author and msg.content != ctx.message.content:
                    message = msg.content
                    break
        
        if not message:
            await ctx.send("❌ **Brak linków YouTube!**\nWklej linki i użyj `!śledź`")
            return
        
        room_name = ctx.channel.name
        result = sledz_system.process_sledz_command(room_name, message)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ **Kanały dodane**",
                description=f"Pokój: **#{room_name}**",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📊 **Rezultat**",
                value=f"```\nNowe: {result['added']}\nJuż były: {result['existing']}\nŁącznie: {result['total']}\n```",
                inline=False
            )
            
            if result.get('forbidden_links'):
                embed.add_field(
                    name="⚠️ **Odrzucone linki**",
                    value=f"```\n{result['forbidden_links']}\n```",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ **Błąd:** {result['error']}")
            
    except Exception as e:
        await ctx.send(f"❌ **Błąd systemu:** {str(e)}")

@bot.command(name="raport", aliases=["r", "report"])
async def raport_command(ctx):
    """Generuje raport CSV dla pokoju Discord"""
    
    import uuid
    response_id = str(uuid.uuid4())[:8]  # Unikalny ID
    
    status_msg = await ctx.send(f"🔄 **Przygotowuję raport...** [ID: {response_id}]")
    
    room_name = str(ctx.channel.name)
    
    # DEBUGGING
    print(f"🔍 DEBUG raport:")
    print(f"   Channel name: '{room_name}'")
    print(f"   Channel type: {type(room_name)}")
    
    channels = config_manager.get_room_channels(room_name)
    print(f"   Found channels: {len(channels)} - {channels}")
    
    # Sprawdź też wszystkie dostępne pokoje
    all_config = config_manager.load_channels_config()
    print(f"   All rooms in config: {list(all_config.get('channels', {}).keys())}")
    
    if not channels:
        embed = discord.Embed(
            title="❌ **Brak kanałów!**",
            description=f"Pokój `#{room_name}` nie ma przypisanych kanałów YouTube.\n\nUżyj `!śledź [link]` aby dodać kanały.",
            color=0xff0000,
            timestamp=datetime.now(timezone.utc)
        )
        
        await status_msg.edit(content="", embed=embed)
        return
    
    # Start generowania
    await status_msg.edit(content=f"📊 **Generuję raport...**\n17-kolumn CSV z {len(channels)} kanałów")
    
    # Generuj raport
    result = raport_system.generate_room_report(room_name, channels)
    
    if result['success']:
        # Commit do GitHub
        git_success = git_manager.auto_commit_and_push(f"Raport {room_name} - {datetime.now().strftime('%Y-%m-%d')}")
        
        embed = discord.Embed(
            title="✅ **Raport gotowy!**",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="📊 **Statystyki**",
            value=f"```\nPokój: #{room_name}\nKanały: {result['channels']}\nFilmy: {result['videos']}\nPlik: {result['filename']}\n```",
            inline=False
        )
        
        embed.add_field(
            name="💾 **17-kolumn CSV**",
            value=f"GitHub: {'✅ PUSH' if git_success else '❌ BŁĄD'}\nSurowe dane YouTube",
            inline=False
        )
        
        await status_msg.edit(content="", embed=embed)
    else:
        embed = discord.Embed(
            title="❌ **Błąd raportu**",
            description=f"```\n{result['error']}\n```",
            color=0xff0000,
            timestamp=datetime.now(timezone.utc)
        )
        
        await status_msg.edit(content="", embed=embed)

@bot.command(name="scheduler")
async def scheduler_command(ctx):
    """Status automatycznych raportów"""
    embed = discord.Embed(
        title="⏰ **Hook Boost 3.0 Scheduler**",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Pobierz aktywne pokoje
    active_rooms = scheduler._get_active_rooms()
    
    embed.add_field(
        name="🔄 **Automatyczne raporty**",
        value="```\nCodziennie o 6:00 UTC\nUltra lean mode\n```",
        inline=False
    )
    
    embed.add_field(
        name="📺 **Aktywne pokoje**",
        value=f"```\n{', '.join(active_rooms) if active_rooms else 'Brak aktywnych pokojów'}\n```",
        inline=False
    )
    
    embed.add_field(
        name="⚡ **Status**",
        value="```\nScheduler: AKTYWNY\nQuota: NIE MONITOROWANE\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="git")
async def git_command(ctx):
    """Status GitHub i auto-commit"""
    embed = discord.Embed(
        title="🔗 **Hook Boost 3.0 GitHub**",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Sprawdź status Git
    git_status = git_manager.setup_git()
    
    embed.add_field(
        name="🔗 **GitHub Integration**",
        value=f"```\nStatus: {'✅ AKTYWNY' if git_status else '❌ NIEAKTYWNY'}\nToken: {'✅ USTAWIONY' if git_manager.github_token else '❌ BRAK'}\n```",
        inline=False
    )
    
    embed.add_field(
        name="📁 **Auto-commit**",
        value="```\nRaporty CSV → GitHub\nCodziennie o 6:00 UTC\n```",
        inline=False
    )
    
    embed.add_field(
        name="⚡ **Ultra Lean**",
        value="```\nBez monitorowania quota\nAutomatyczne backup\n```",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Simple HTTP server for Render.com port detection
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hook Boost 3.0 Discord Bot is running!')

def start_http_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHandler)
    server.serve_forever()

# ===== URUCHOMIENIE =====

if __name__ == "__main__":
    print(f"🚀 Uruchamianie Hook Boost 3.0...")
    print(f"🔧 Discord Token: {'✅ Ustawiony' if DISCORD_TOKEN and DISCORD_TOKEN != 'DEMO_TOKEN' else '❌ BRAK'}")
    print(f"🔧 YouTube API: {'✅ Ustawiony' if YOUTUBE_API_KEY and YOUTUBE_API_KEY != 'DEMO_KEY' else '❌ BRAK'}")
    print(f"🔧 GitHub Token: {'✅ Ustawiony' if GITHUB_TOKEN else '❌ BRAK'}")
    
    # Test Git
    import subprocess
    try:
        git_version = subprocess.run(['git', '--version'], capture_output=True, text=True)
        print(f"🔧 Git: {git_version.stdout.strip() if git_version.returncode == 0 else '❌ BRAK'}")
    except Exception as e:
        print(f"🔧 Git: ❌ BŁĄD - {e}")
    
    # Start HTTP server in background for Render.com
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print(f"🌐 HTTP server started on port 8000")
    
    # Inicjalizacja systemów z obsługą błędów
    try:
        config_manager = ConfigManager()
        print("✅ ConfigManager zainicjalizowany")
    except Exception as e:
        print(f"❌ Błąd ConfigManager: {e}")
        print(f"   {traceback.format_exc()}")
    
    try:
        sledz_system = SledzSystem(config_manager)
        print("✅ SledzSystem zainicjalizowany")
    except Exception as e:
        print(f"❌ Błąd SledzSystem: {e}")
        print(f"   {traceback.format_exc()}")
    
    try:
        raport_system = RaportSystem(YOUTUBE_API_KEY)
        print("✅ RaportSystem zainicjalizowany")
    except Exception as e:
        print(f"❌ Błąd RaportSystem: {e}")
        print(f"   {traceback.format_exc()}")
    
    try:
        scheduler = AutoScheduler(raport_system, config_manager)
        print("✅ AutoScheduler zainicjalizowany")
    except Exception as e:
        print(f"❌ Błąd AutoScheduler: {e}")
        print(f"   {traceback.format_exc()}")
    
    try:
        git_manager = GitManager(GITHUB_TOKEN)
        print("✅ GitManager zainicjalizowany")
    except Exception as e:
        print(f"❌ Błąd GitManager: {e}")
        print(f"   {traceback.format_exc()}")
    
    print(f"🚀 Uruchamianie Discord bot...")
    
    # Uruchomienie bota z retry i obsługą błędów
    max_retries = 3
    for attempt in range(max_retries):
        try:
            bot.run(DISCORD_TOKEN)
        except Exception as e:
            print(f"❌ Błąd uruchomienia bota (próba {attempt + 1}/{max_retries}): {e}")
            print(f"   {traceback.format_exc()}")
            if attempt < max_retries - 1:
                print(f"⏳ Ponowna próba za 5 sekund...")
                time.sleep(5)
            else:
                print(f"💀 Nie udało się uruchomić bota po {max_retries} próbach")
                break
    
    # Keep the container alive
    print("🔄 Bot zakończony, utrzymuję kontener...")
    while True:
        time.sleep(30) 