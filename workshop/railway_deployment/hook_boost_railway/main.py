#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 HOOK BOOST V2 - ULTRA LEAN RAILWAY  
====================================

Ultra-lekki bot do zbierania surowych danych YouTube:
- !śledź - dodawanie kanałów  
- !raport - generowanie 17-kolumnowego CSV
- Bez quota managera - sprawdzasz quota na stronie Google
- Multi-room support

AUTOR: Hook Boost V2 - Ultra Lean Edition
WERSJA: 3.0 (Lean Railway)
"""

import os
import discord  
from discord.ext import commands
import json
from datetime import datetime, timezone
import sys

# ===== KONFIGURACJA BOTA =====

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not DISCORD_TOKEN or not YOUTUBE_API_KEY:
    print("❌ Brak wymaganych zmiennych środowiskowych:")
    print("   - DISCORD_TOKEN") 
    print("   - YOUTUBE_API_KEY")
    sys.exit(1)

# ===== DISCORD BOT SETUP =====

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

print("🚀 HOOK BOOST V2 - ULTRA LEAN RAILWAY")
print("   17-kolumnowy CSV generator")
print("   Multi-room support")
print("   Quota monitoring: Google Console")

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
        name="!raport | Ultra Lean Mode"
    )
    await bot.change_presence(activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """Obsługa błędów"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Nieznana komenda!** Użyj \`!pomoc\`")
    else:
        await ctx.send(f"❌ **Błąd:** {str(error)}")
        print(f"Błąd komendy: {error}")

# ===== KOMENDY =====

@bot.command(name="pomoc", aliases=["help", "h"])
async def help_command(ctx):
    """Pokazuje listę dostępnych komend"""
    embed = discord.Embed(
        title="🚀 **HOOK BOOST V2** - Ultra Lean Mode",
        description="Bot do zbierania surowych danych YouTube (17-kolumnowy CSV)",
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="📺 **Zarządzanie kanałami**",
        value="\`!śledź [linki]\` - Dodaje kanały do tego pokoju\n"
              "\`!raport\` - Generuje 17-kolumnowy CSV",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ **Informacje**",
        value="\`!status\` - Status systemu\n"
              "\`!pomoc\` - Ta wiadomość",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **Ultra Lean Philosophy**",
        value="• Każdy pokój ma swoje kanały\n• Surowe dane bez analizy\n• 17-kolumnowy CSV output\n• Quota monitoring: Google Console",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="status")
async def status_command(ctx):
    """Status systemu HOOK BOOST V2 - Ultra Lean"""
    try:
        embed = discord.Embed(
            title="🤖 **STATUS HOOK BOOST V2**",
            description="Ultra Lean Railway Mode",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🚀 **Wersja**",
            value="\`\`\`\nHook Boost V2 - Ultra Lean\nWersja: 3.0\nMode: Railway Production\n\`\`\`",
            inline=False
        )
        
        embed.add_field(
            name="⛽ **Quota Monitoring**",
            value="\`\`\`\nLocal Manager: DISABLED\nMonitoring: Google Console\nMode: Manual Check\n\`\`\`",
            inline=False
        )
        
        embed.add_field(
            name="📊 **Output Format**",
            value="\`\`\`\n17-kolumnowy CSV\nSurowe metadane YouTube\nAuto-commit GitHub\n\`\`\`",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD STATUS**\n{str(e)}")

# ===== URUCHOMIENIE BOTA =====

if __name__ == "__main__":
    print("🚀 HOOK BOOST V2 - ULTRA LEAN RAILWAY")
    print("   17-kolumnowy CSV generator")
    print("   Starting...")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Błąd uruchomienia bota: {e}")

        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD STATUS**\n{str(e)}")

@bot.command(name="śledź")  
async def sledz_command(ctx, *, message: str = None):
    """Dodaje kanały YouTube do śledzenia dla tego pokoju"""
    try:
        from sledz_system import SledzSystem, create_forbidden_links_embed, create_success_embed
        
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
            await ctx.send(embed=embed)
            return
        
        sledz_system = SledzSystem(api_key=YOUTUBE_API_KEY)
        result = sledz_system.process_sledz_command(ctx.channel.name, message)
        
        if result["success"]:
            await ctx.send("✅ **ŚLEDZENIE ZAKTUALIZOWANE**")
        else:
            await ctx.send(f"❌ **BŁĄD:** {result.get(\"error\", \"Nieznany\")}")
                
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU:** {str(e)}")

@bot.command(name="raport")
async def raport_command(ctx):
    """Generuje 17-kolumnowy CSV raport"""
    try:
        from raport_system_workshop import RaportSystemWorkshop
        from sledz_system import SledzSystem
        
        sledz_system = SledzSystem()
        room_channels = sledz_system.get_room_channels(ctx.channel.name)
        
        if not room_channels:
            await ctx.send("❌ **BRAK KANAŁÓW** - Użyj \`!śledź\`")
            return
        
        await ctx.send(f"📊 **Generuję CSV** z {len(room_channels)} kanałów...")
        
        raport_system = RaportSystemWorkshop(
            api_key=YOUTUBE_API_KEY,
            quota_manager=None,
            demo_mode=False
        )
        
        result = raport_system.collect_room_data(ctx.channel.name, room_channels)
        
        if result["success"]:
            await ctx.send("✅ **RAPORT GOTOWY** - 17-kolumnowy CSV")
        else:
            await ctx.send(f"❌ **BŁĄD:** {result.get(\"error\", \"Nieznany\")}")
                      
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU:** {str(e)}")

if __name__ == "__main__":
    print("🚀 HOOK BOOST V2 - ULTRA LEAN RAILWAY")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Błąd uruchomienia: {e}")
