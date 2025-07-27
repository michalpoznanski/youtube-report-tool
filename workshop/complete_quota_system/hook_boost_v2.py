#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 HOOK BOOST V2 - YouTube Analytics Discord Bot
===============================================

Nowy bot z modularną architekturą i czystym kodem.
FILOZOFIA: Każdy pokój ma swoje kanały, proste komendy, bezpieczne quota.

GŁÓWNE KOMENDY:
- !sledz  - Dodawanie kanałów do pokoju
- !raport - Zbieranie danych YouTube  
- !name   - Analiza nazwisk
- !paliwo - Status quota API

AUTOR: Rebuild 2025-07-26
WERSJA: 2.0.0
"""

import os
import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
import sys

# ===== KONFIGURACJA BOTA =====

# Załaduj zmienne środowiskowe
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

if not DISCORD_TOKEN or not YOUTUBE_API_KEY:
    print("❌ BRAK KLUCZY API!")
    print("   Uruchom: source config/env_setup.sh")
    print("   Następnie: python3 hook_boost_v2.py")
    sys.exit(1)

# Konfiguracja Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    description='🚀 HOOK BOOST V2 - YouTube Analytics Bot',
    help_command=None  # Wyłącz domyślną komendę help
)

# Inicjalizacja modułów
quota_manager = None
try:
    from quota_manager import QuotaManager
    quota_manager = QuotaManager(YOUTUBE_API_KEY)
    print("✅ QuotaManager załadowany")
except ImportError:
    print("⚠️ QuotaManager niedostępny")

# ===== EVENTY BOTA =====

@bot.event
async def on_ready():
    """Wydarzenie uruchomienia bota"""
    print(f"\n🚀 HOOK BOOST V2 URUCHOMIONY!")
    print(f"   Bot: {bot.user.name}")
    print(f"   ID: {bot.user.id}")
    print(f"   Serwery: {len(bot.guilds)}")
    print(f"   Użytkownicy: {len(set(bot.get_all_members()))}")
    
    # Ustaw status bota
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="YouTube Analytics 📊"
    )
    await bot.change_presence(activity=activity)
    
    print(f"✅ HOOK BOOST V2 gotowy do pracy!")

@bot.event
async def on_command_error(ctx, error):
    """Obsługa błędów komend"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ **Nieznana komenda**\nUżyj `!pomoc` aby zobaczyć dostępne komendy.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Brak argumentów**\n{error}")
    else:
        await ctx.send(f"❌ **Błąd**: {error}")
        print(f"Błąd komendy: {error}")

# ===== KOMENDY GŁÓWNE =====

@bot.command(name='pomoc', aliases=['help', 'h'])
async def help_command(ctx):
    """Wyświetla pomoc i dostępne komendy"""
    embed = discord.Embed(
        title="🚀 **HOOK BOOST V2 - POMOC**",
        description="YouTube Analytics Bot z modularną architekturą",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="📺 **!śledź** - Dodawanie kanałów",
        value="```\n!śledź [linki YouTube]\nDodaje kanały do tego pokoju\n```",
        inline=False
    )
    
    embed.add_field(
        name="📊 **!raport** - Zbieranie danych",
        value="```\n!raport\nZbiera dane z kanałów tego pokoju\n```",
        inline=False
    )
    
    embed.add_field(
        name="🔍 **!name** - Analiza nazwisk",
        value="```\n!name\nAnalizuje nazwiska z raportów\n```",
        inline=False
    )
    
    embed.add_field(
        name="⛽ **!paliwo** - Status quota",
        value="```\n!paliwo\nSprawdza zużycie quota API\n```",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ **Informacje**",
        value="• Każdy pokój ma swoje kanały\n• Kanały mogą być w wielu pokojach\n• Bot oszczędza quota API",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='śledź')
async def sledz_command(ctx, *, message: str = None):
    """
    Dodaje kanały YouTube do śledzenia dla tego pokoju
    Obsługuje @handle (1 quota) i Channel ID (0 quota)
    """
    try:
        # Import modułu śledzenia
        from sledz_system import SledzSystem, create_forbidden_links_embed, create_success_embed
        
        # Sprawdź czy są linki
        if not message:
            async for msg in ctx.channel.history(limit=2):
                if msg.author == ctx.author and msg.content != ctx.message.content:
                    message = msg.content
                    break
        
        if not message:
            embed = discord.Embed(
                title="❌ **BRAK LINKÓW**",
                description="Wklej linki YouTube w wiadomości",
                color=0xff0000
            )
            embed.add_field(
                name="✅ **Dozwolone formaty**",
                value="```\n@handle:\nhttps://www.youtube.com/@pudelektv\n\nChannel ID:\nUCShUU9VW-unGNHC-3XMUSmQ\n```",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Inicjalizuj system śledzenia
        sledz_system = SledzSystem(api_key=YOUTUBE_API_KEY)
        
        # Przetwórz komendę
        result = sledz_system.process_sledz_command(ctx.channel.name, message)
        
        if result['success']:
            # Sukces - użyj nowego embed
            embed_data = create_success_embed(result['analysis'], ctx.channel.name)
            embed = discord.Embed(
                title=embed_data['title'],
                description=embed_data['description'],
                color=embed_data['color'],
                timestamp=datetime.now(timezone.utc)
            )
            
            for field in embed_data['fields']:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field['inline']
                )
            
            # Dodaj statystyki rzeczywiste
            add_result = result['add_result']
            embed.add_field(
                name="📈 **Statystyki**",
                value=f"```\nNowe kanały: {len(add_result['new_channels'])}\nJuż śledzone: {len(add_result['already_tracked'])}\nŁącznie w pokoju: {add_result['total_in_room']}\n```",
                inline=False
            )
            
            embed.add_field(
                name="🔄 **Następne kroki**",
                value="• Użyj `!raport` aby zebrać dane\n• Użyj `!name` aby analizować nazwiska",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        else:
            # Błąd - użyj nowego forbidden embed
            if result.get('analysis') and result['analysis']['forbidden_links'] > 0:
                embed_data = create_forbidden_links_embed(result['analysis'])
                embed = discord.Embed(
                    title=embed_data['title'],
                    description=embed_data['description'],
                    color=embed_data['color']
                )
                
                for field in embed_data['fields']:
                    embed.add_field(
                        name=field['name'],
                        value=field['value'],
                        inline=field['inline']
                    )
                
                await ctx.send(embed=embed)
            else:
                # Inny błąd
                await ctx.send(f"❌ **BŁĄD**\n{result['error']}")
                
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU**\n{str(e)}")

@bot.command(name='raport')
async def raport_command(ctx):
    """
    Zbiera dane z kanałów tego pokoju
    Użycie: !raport
    """
    await ctx.send("🚧 **KOMENDA W BUDOWIE**\n"
                   "System !raport będzie dostępny w następnej sesji.\n"
                   "Na razie użyj `!śledź` aby dodać kanały.")

@bot.command(name='name')  
async def name_command(ctx):
    """
    Analizuje nazwiska z raportów
    Użycie: !name
    """
    await ctx.send("🚧 **KOMENDA W BUDOWIE**\n"
                   "System !name będzie dostępny po zaimplementowaniu !raport.")

@bot.command(name='paliwo')
async def paliwo_command(ctx):
    """Sprawdza status quota API"""
    if not quota_manager:
        await ctx.send("❌ **QUOTA MANAGER NIEDOSTĘPNY**")
        return
    
    try:
        summary = quota_manager.get_quota_summary()
        
        today_usage = summary.get('today_usage', 0)
        daily_limit = summary.get('daily_limit', 10000)
        
        embed = discord.Embed(
            title="⛽ **STATUS QUOTA API**",
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Dzisiejsze zużycie
        embed.add_field(
            name="📊 **Dzisiejsze zużycie**",
            value=f"```\n{today_usage:,}/{daily_limit:,} punktów\n```",
            inline=False
        )
        
        # Info o koszcie komendy
        embed.add_field(
            name="💰 **Koszt sprawdzenia**",
            value="```\nTa komenda kosztuje 100 quota\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD QUOTA**: {str(e)}")

@bot.command(name='status')
async def status_command(ctx):
    """Status systemu HOOK BOOST V2"""
    embed = discord.Embed(
        title="🚀 **HOOK BOOST V2 STATUS**",
        color=0x0099ff,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="🤖 **Bot**",
        value=f"```\nWersja: 2.0.0\nUptime: Online\nSerwery: {len(bot.guilds)}\n```",
        inline=True
    )
    
    embed.add_field(
        name="🔧 **Moduły**",
        value=f"```\nSledzSystem: {'✅' if 'sledz_system' in sys.modules else '❌'}\nQuotaManager: {'✅' if quota_manager else '❌'}\n```",
        inline=True
    )
    
    embed.add_field(
        name="🔑 **API**",
        value=f"```\nYouTube: {'✅' if YOUTUBE_API_KEY else '❌'}\nDiscord: {'✅' if DISCORD_TOKEN else '❌'}\n```",
        inline=True
    )
    
    await ctx.send(embed=embed)

# ===== URUCHOMIENIE BOTA =====

if __name__ == "__main__":
    print("🚀 Uruchamiam HOOK BOOST V2...")
    print("   Sprawdzam konfigurację...")
    
    if not DISCORD_TOKEN:
        print("❌ Brak DISCORD_TOKEN!")
        sys.exit(1)
    
    if not YOUTUBE_API_KEY:
        print("❌ Brak YOUTUBE_API_KEY!")  
        sys.exit(1)
    
    print("✅ Konfiguracja OK")
    print("   Łączę z Discord...")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Błąd uruchomienia: {e}")
        sys.exit(1) 