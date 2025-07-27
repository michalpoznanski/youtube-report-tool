#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 QUOTA DISPLAY V2 - Warsztat ulepszeń !paliwo
===============================================

Cel: Prosty, przejrzysty komunikat quota - bez zbędnych informacji.
"""

import discord
from datetime import datetime, timezone

class QuotaDisplayV2:
    """Ulepszone wyświetlanie quota dla Discord"""
    
    def __init__(self, quota_manager):
        self.quota_manager = quota_manager
        
    def create_quota_embed(self):
        """Tworzy prosty embed z informacjami o quota"""
        
        summary = self.quota_manager.get_quota_summary()
        
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
        
        return embed

# PRZYKŁAD UŻYCIA W HOOK_BOOST_V2.PY:

"""
@bot.command(name='paliwo')
async def paliwo_command(ctx):
    if not quota_manager:
        await ctx.send("❌ **QUOTA MANAGER NIEDOSTĘPNY**")
        return
    
    try:
        display = QuotaDisplayV2(quota_manager)
        embed = display.create_quota_embed()
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD**: {str(e)}")
""" 