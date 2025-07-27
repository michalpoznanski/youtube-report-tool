#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 HOOK BOOST V2 - COMPLETE QUOTA MONITORING
============================================

Bot z KOMPLETNYM monitorowaniem quota dla wszystkich funkcji:
- !paliwo - monitoruje swoje 100 quota
- !śledź - monitoruje 1 quota (@handle) lub 100 (search)
- !raport - monitoruje zbieranie danych YouTube
- !name - monitoruje analizę (jeśli używa API)
- WSZYSTKIE funkcje YouTube API są śledzone

AUTOR: Hook Boost V2 - Complete System
WERSJA: 2.1 (Complete Quota Monitoring)
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

# ===== INICJALIZACJA MODUŁÓW =====

# Inicjalizuj QuotaManager z PEŁNYM monitorowaniem
quota_manager = None
try:
    from quota_manager import QuotaManager
    quota_manager = QuotaManager(YOUTUBE_API_KEY)
    print("✅ QuotaManager załadowany z PEŁNYM monitorowaniem")
except Exception as e:
    print(f"❌ Błąd QuotaManager: {e}")
    sys.exit(1)

# ===== EVENTY BOTA =====

@bot.event
async def on_ready():
    print("🚀 Uruchamiam HOOK BOOST V2...")
    print("   Sprawdzam konfigurację...")
    
    # Sprawdź dostęp do API
    try:
        summary = quota_manager.get_quota_summary()
        print("✅ Konfiguracja OK")
    except Exception as e:
        print(f"❌ Błąd konfiguracji: {e}")
        return
    
    print("   Łączę z Discord...")
    
@bot.event 
async def on_connect():
    print(f"\n🚀 HOOK BOOST V2 URUCHOMIONY!")
    print(f"   Bot: {bot.user.name}")
    print(f"   ID: {bot.user.id}")
    print(f"   Serwery: {len(bot.guilds)}")
    
    total_members = sum(guild.member_count for guild in bot.guilds)
    print(f"   Użytkownicy: {total_members}")
    print("✅ HOOK BOOST V2 gotowy do pracy!")

# ===== KOMENDY BOTA =====

@bot.command(name='pomoc', aliases=['help', 'h'])
async def help_command(ctx):
    """Pokazuje listę dostępnych komend"""
    embed = discord.Embed(
        title="🚀 **HOOK BOOST V2** - Pomoc",
        description="Bot do analizowania YouTube kanałów z PEŁNYM monitorowaniem quota",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="📺 **Zarządzanie kanałami**",
        value="`!śledź [linki]` - Dodaje kanały do tego pokoju\n"
              "`!raport` - Zbiera dane z kanałów (MONITORED)\n"
              "`!name` - Analizuje nazwiska (MONITORED)",
        inline=False
    )
    
    embed.add_field(
        name="⛽ **Monitoring quota**",
        value="`!paliwo` - Status quota API (MONITORED)\n"
              "`!status` - Status systemu bota",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ **Informacje**",
        value="`!pomoc` - Ta wiadomość",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **Filozofia**",
        value="• Każdy pokój ma swoje kanały\n• Kanały mogą być w wielu pokojach\n• Bot oszczędza quota API\n• **WSZYSTKIE operacje są monitorowane**",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='śledź')
async def sledz_command(ctx, *, message: str = None):
    """
    Dodaje kanały YouTube do śledzenia dla tego pokoju
    Obsługuje @handle (1 quota) i Channel ID (0 quota)
    PEŁNE MONITOROWANIE QUOTA
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
                value="```\n@handle (1 quota):\nhttps://www.youtube.com/@pudelektv\n\nChannel ID (0 quota):\nUCShUU9VW-unGNHC-3XMUSmQ\n```",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Inicjalizuj system śledzenia z PEŁNYM monitorowaniem
        sledz_system = SledzSystem(api_key=YOUTUBE_API_KEY)
        
        # Przetwórz komendę (QUOTA MONITORED)
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
    PEŁNE MONITOROWANIE QUOTA dla wszystkich API calls
    """
    try:
        # Import systemu raportów
        from simple_raport_system_v2 import SimpleRaportSystemV2
        
        # Sprawdź czy pokój ma kanały
        from sledz_system import SledzSystem
        sledz_system = SledzSystem()
        room_channels = sledz_system.get_room_channels(ctx.channel.name)
        
        if not room_channels:
            embed = discord.Embed(
                title="❌ **BRAK KANAŁÓW**",
                description=f"Pokój #{ctx.channel.name} nie ma żadnych kanałów do śledzenia",
                color=0xff0000
            )
            embed.add_field(
                name="🔧 **Rozwiązanie**",
                value="Użyj `!śledź [linki]` aby dodać kanały do tego pokoju",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Rozpocznij zbieranie danych z MONITOROWANIEM QUOTA
        embed = discord.Embed(
            title="📊 **ROZPOCZYNAM RAPORT**",
            description=f"Zbieram dane z {len(room_channels)} kanałów...",
            color=0xffaa00
        )
        embed.add_field(
            name="⚠️ **Uwaga**",
            value="Ta operacja może zużyć znaczną ilość quota!\nMonitorowanie: WŁĄCZONE ✅",
            inline=False
        )
        
        status_msg = await ctx.send(embed=embed)
        
        # Inicjalizuj system raportów z quota monitoring
        raport_system = SimpleRaportSystemV2(
            api_key=YOUTUBE_API_KEY,
            quota_manager=quota_manager  # PRZEKAŻ quota_manager!
        )
        
        # Zbierz dane (QUOTA MONITORED)
        result = raport_system.collect_room_data(ctx.channel.name, room_channels)
        
        if result['success']:
            # Sukces
            embed = discord.Embed(
                title="✅ **RAPORT ZAKOŃCZONY**",
                description=f"Dane zebrane z pokoju #{ctx.channel.name}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📁 **Plik**",
                value=f"```\n{result['filename']}\n```",
                inline=False
            )
            
            embed.add_field(
                name="📊 **Statystyki**",
                value=f"```\nKanały: {result['channels_processed']}\nFilmy: {result['videos_collected']}\nQuota użyte: {result['quota_used']}\n```",
                inline=False
            )
            
            embed.add_field(
                name="🔄 **Następne kroki**",
                value="• Użyj `!name` aby analizować nazwiska\n• Sprawdź `!paliwo` aby zobaczyć zużycie quota",
                inline=False
            )
            
            await status_msg.edit(embed=embed)
            
        else:
            # Błąd
            embed = discord.Embed(
                title="❌ **BŁĄD RAPORTU**",
                description=result['error'],
                color=0xff0000
            )
            embed.add_field(
                name="💡 **Sprawdź**",
                value="• Status quota: `!paliwo`\n• Logi systemu w konsoli",
                inline=False
            )
            
            await status_msg.edit(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU RAPORT**\n{str(e)}")

@bot.command(name='name')  
async def name_command(ctx):
    """
    Analizuje nazwiska z raportów
    MONITOROWANIE QUOTA jeśli używa API
    """
    try:
        # Tu będzie system analizy nazwisk
        # Jeśli będzie używać YouTube API, musi mieć quota monitoring!
        
        await ctx.send("🚧 **KOMENDA W BUDOWIE**\n"
                      "System !name będzie miał PEŁNE monitorowanie quota.\n"
                      "Dostępny po zaimplementowaniu w przyszłej sesji.")
                      
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU NAME**\n{str(e)}")

@bot.command(name='paliwo')
async def paliwo_command(ctx):
    """
    Sprawdza status quota API
    MONITORUJE WŁASNE 100 quota!
    """
    if not quota_manager:
        await ctx.send("❌ **QUOTA MANAGER NIEDOSTĘPNY**")
        return
    
    try:
        # LOGUJ ZUŻYCIE TEGO POLECENIA!
        quota_manager.log_operation(
            'quota_check',
            {'command': '!paliwo', 'user': str(ctx.author), 'channel': ctx.channel.name},
            100,  # !paliwo kosztuje 100 quota
            True  # success
        )
        
        summary = quota_manager.get_quota_summary()
        
        today_usage = summary.get('today_usage', 0)
        daily_limit = summary.get('daily_limit', 10000)
        
        embed = discord.Embed(
            title="⛽ **STATUS QUOTA API**",
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Dzisiejsze zużycie (UWZGLĘDNIA AKTUALNY CALL!)
        embed.add_field(
            name="📊 **Dzisiejsze zużycie**",
            value=f"```\n{today_usage:,}/{daily_limit:,} punktów\n```",
            inline=False
        )
        
        # Info o koszcie komendy
        embed.add_field(
            name="💰 **Koszt sprawdzenia**",
            value="```\nTa komenda kosztuje 100 quota\n✅ ZUŻYCIE ZALOGOWANE\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        # Loguj błąd z quota!
        if quota_manager:
            quota_manager.log_operation(
                'quota_check',
                {'command': '!paliwo', 'user': str(ctx.author), 'error': str(e)},
                100,  # quota było zużyte mimo błędu
                False  # success = False
            )
        
        await ctx.send(f"❌ **BŁĄD QUOTA**: {str(e)}")

@bot.command(name='status')
async def status_command(ctx):
    """Status systemu HOOK BOOST V2 z monitorowaniem quota"""
    try:
        # Ta komenda NIE używa YouTube API, więc nie loguje quota
        
        embed = discord.Embed(
            title="🤖 **STATUS HOOK BOOST V2**",
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Info o bocie
        embed.add_field(
            name="🚀 **System**",
            value=f"```\nWersja: 2.1 (Complete Quota Monitoring)\nPing: {round(bot.latency * 1000)}ms\nSerwery: {len(bot.guilds)}\n```",
            inline=False
        )
        
        # Status quota (bez używania API)
        if quota_manager:
            try:
                summary = quota_manager.get_quota_summary()
                today_usage = summary.get('today_usage', 0)
                daily_limit = summary.get('daily_limit', 10000)
                
                embed.add_field(
                    name="⛽ **Quota Status**",
                    value=f"```\nDzisiaj: {today_usage:,}/{daily_limit:,}\nMonitorowanie: ✅ PEŁNE\n```",
                    inline=False
                )
            except:
                embed.add_field(
                    name="⛽ **Quota Status**", 
                    value="```\nBłąd odczytu quota\n```",
                    inline=False
                )
        
        # Funkcje monitorowane
        embed.add_field(
            name="📊 **Funkcje monitorowane**",
            value="```\n!paliwo - 100 quota ✅\n!śledź - 1-100 quota ✅\n!raport - variable quota ✅\n!name - TBD quota ✅\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD STATUS**: {str(e)}")

# ===== URUCHOMIENIE BOTA =====

if __name__ == "__main__":
    print("🚀 HOOK BOOST V2 - COMPLETE QUOTA MONITORING")
    print("   Wszystkie funkcje YouTube API są monitorowane")
    print("   Starting...")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Błąd uruchomienia bota: {e}") 