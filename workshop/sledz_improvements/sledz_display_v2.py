#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎨 SLEDZ DISPLAY V2 - Nowy interfejs !śledź
==========================================

Cel: Pokazywać liczby kanałów zamiast nazw + koszty quota
"""

import discord
from datetime import datetime, timezone

class SledzDisplayV2:
    """Nowy interfejs wyświetlania wyników !śledź"""
    
    def create_sledz_embed(self, result):
        """Tworzy embed z wynikami !śledź - bez nazw kanałów, z kosztami"""
        
        if not result['success']:
            # Embed błędu
            embed = discord.Embed(
                title="❌ **BŁĄD DODAWANIA KANAŁÓW**",
                description=result['error'],
                color=0xff0000,
                timestamp=datetime.now(timezone.utc)
            )
            return embed
        
        add_result = result['add_result']
        quota_cost = result.get('quota_cost', 0)
        
        # Kolor zależny od kosztu quota
        if quota_cost == 0:
            color = 0x00ff00  # Zielony - darmowe
        elif quota_cost <= 5:
            color = 0xffa500  # Pomarańczowy - akceptowalne
        else:
            color = 0xff0000  # Czerwony - drogie
        
        embed = discord.Embed(
            title="✅ **KANAŁY PRZETWORZONE**",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Podsumowanie liczbowe - BEZ NAZW
        total_new = len(add_result.get('new_channels', []))
        total_existing = len(add_result.get('already_tracked', []))
        total_in_room = add_result.get('total_in_room', 0)
        
        embed.add_field(
            name="📊 **Wyniki**",
            value=f"```\n"
                  f"Nowe kanały: {total_new}\n"
                  f"Już śledzone: {total_existing}\n"
                  f"Łącznie w pokoju: {total_in_room}\n"
                  f"```",
            inline=True
        )
        
        # Koszt quota
        embed.add_field(
            name="💰 **Koszt quota**",
            value=f"```\n{quota_cost} punktów\n```",
            inline=True
        )
        
        # Jeśli był kosztowne, dodaj ostrzeżenie
        if quota_cost > 10:
            embed.add_field(
                name="⚠️ **Uwaga**",
                value="Wykryto kosztowne operacje!\nUżywaj linków z Channel ID lub @handle",
                inline=False
            )
        
        # Następne kroki - tylko jeśli dodano nowe
        if total_new > 0:
            embed.add_field(
                name="🔄 **Następne kroki**",
                value="• Użyj `!raport` aby zebrać dane\n• Użyj `!name` aby analizować treść",
                inline=False
            )
        
        return embed
    
    def create_quota_warning_embed(self, estimated_cost, available_quota):
        """Tworzy embed ostrzeżenia o wysokich kosztach quota"""
        
        embed = discord.Embed(
            title="⚠️ **OSTRZEŻENIE QUOTA**",
            description=f"Szacowany koszt: **{estimated_cost} quota**",
            color=0xff8c00,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="📊 **Status quota**",
            value=f"```\nDostępne: {available_quota}\nKoszt operacji: {estimated_cost}\n```",
            inline=False
        )
        
        embed.add_field(
            name="💡 **Jak obniżyć koszty?**",
            value="• Używaj linków z Channel ID\n• Używaj @handle zamiast /c/nazwa\n• Unikaj linków do filmów",
            inline=False
        )
        
        embed.add_field(
            name="❓ **Kontynuować?**",
            value="Użyj ponownie `!śledź` aby potwierdzić",
            inline=False
        )
        
        return embed

# PRZYKŁAD NOWEGO INTERFEJSU:

"""
STARY INTERFEJS:
✅ KANAŁY DODANE
📍 Pokój: #showbiz
🆕 Nowe kanały (1)
• UCShUU9VW-unGNHC-3XMUSmQ...
📊 Podsumowanie
# Łącznie w pokoju: 22
# Dodano nowych: 1  
# Koszt quota: 0 punktów

NOWY INTERFEJS:
✅ KANAŁY PRZETWORZONE
📊 Wyniki
Nowe kanały: 1
Już śledzone: 0
Łącznie w pokoju: 22

💰 Koszt quota
0 punktów

🔄 Następne kroki  
• Użyj !raport aby zebrać dane
• Użyj !name aby analizować treść
"""

if __name__ == "__main__":
    print("🎨 Sledz Display V2 - Nowy interfejs")
    print("   Funkcje:")
    print("   - create_sledz_embed() - Główny embed bez nazw kanałów")
    print("   - create_quota_warning_embed() - Ostrzeżenie o kosztach")
    print("   - Kolorowe statusy według kosztu quota")
    print("   - Skupienie na liczbach, nie nazwach") 