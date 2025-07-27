@bot.command(name='śledź')
async def track_channels(ctx, *, message: str = None):
    """
    Dodaje kanały YouTube do śledzenia dla konkretnego pokoju Discord
    Nowa filozofia: każdy pokój ma swoje kanały (bez kategorii)
    Użycie: !śledź [linki YouTube w wiadomości]
    """
    try:
        # Import nowego systemu
        from sledz_system import SledzSystem
        
        # Jeśli nie ma argumentu, sprawdź poprzednią wiadomość
        if not message:
            async for msg in ctx.channel.history(limit=2):
                if msg.author == ctx.author and msg.content != ctx.message.content:
                    message = msg.content
                    break
        
        if not message:
            await ctx.send("❌ **BRAK LINKÓW**\nWklej linki YouTube w tej samej wiadomości lub w poprzedniej.")
            return
        
        # Inicjalizuj nowy system śledzenia
        sledz_system = SledzSystem(api_key=YOUTUBE_API_KEY)
        
        # Przetwórz komendę
        result = sledz_system.process_sledz_command(ctx.channel.name, message)
        
        if result['success']:
            # Zaktualizuj globalną konfigurację bota
            global CHANNELS_CONFIG
            if hasattr(sledz_system, 'channels_config'):
                CHANNELS_CONFIG = sledz_system.channels_config
            
            # Przygotuj embed z wynikami
            embed = discord.Embed(
                title="✅ **KANAŁY DODANE DO ŚLEDZENIA**",
                description=f"📍 **Pokój:** #{ctx.channel.name}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            add_result = result['add_result']
            
            if add_result['new_channels']:
                embed.add_field(
                    name=f"🆕 **Nowe kanały** ({len(add_result['new_channels'])})",
                    value="```\n" + "\n".join([f"• {ch[:20]}..." for ch in add_result['new_channels'][:5]]) + 
                          (f"\n... i {len(add_result['new_channels'])-5} więcej" if len(add_result['new_channels']) > 5 else "") + "\n```",
                    inline=False
                )
            
            if add_result['already_tracked']:
                embed.add_field(
                    name=f"🔄 **Już śledzone** ({len(add_result['already_tracked'])})",
                    value="```\n" + "\n".join([f"• {ch[:20]}..." for ch in add_result['already_tracked'][:3]]) + 
                          (f"\n... i {len(add_result['already_tracked'])-3} więcej" if len(add_result['already_tracked']) > 3 else "") + "\n```",
                    inline=False
                )
            
            if add_result['cross_room_channels']:
                cross_info = []
                for channel_id, other_room in add_result['cross_room_channels'][:3]:
                    cross_info.append(f"• {channel_id[:20]}... (też w: #{other_room})")
                
                embed.add_field(
                    name=f"🔄 **Kanały w wielu pokojach** ({len(add_result['cross_room_channels'])})",
                    value="```\n" + "\n".join(cross_info) + 
                          (f"\n... i {len(add_result['cross_room_channels'])-3} więcej" if len(add_result['cross_room_channels']) > 3 else "") + "\n```",
                    inline=False
                )
            
            embed.add_field(
                name="📊 **Podsumowanie**",
                value=f"```md\n"
                      f"# Łącznie w pokoju #{ctx.channel.name}: {add_result['total_in_room']}\n"
                      f"# Dodano nowych: {len(add_result['new_channels'])}\n"
                      f"# Już istniało: {len(add_result['already_tracked'])}\n"
                      f"# Znalezione linki: {result['found_links']['total']}\n"
                      f"# Koszt quota: {result['quota_cost']} punktów\n"
                      f"```",
                inline=False
            )
            
            embed.add_field(
                name="🔄 **Następne kroki**",
                value="• Użyj `!raport` aby zebrać dane z kanałów tego pokoju\n"
                      "• Użyj `!name` aby analizować zebrane nazwiska\n"
                      "• Konfiguracja została automatycznie zapisana",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        else:
            # Obsługa błędów
            if result['error'] == 'Niewystarczające quota':
                embed = discord.Embed(
                    title="⛽ **NIEWYSTARCZAJĄCE QUOTA**",
                    description="Nie można wykonać operacji z powodu ograniczeń API",
                    color=0xff0000
                )
                embed.add_field(
                    name="💰 **Szacowany koszt**",
                    value=f"```\n{result['quota_cost']} punktów quota\n```",
                    inline=False
                )
                embed.add_field(
                    name="💡 **Rozwiązania**",
                    value="• Poczekaj do północy UTC na reset quota\n"
                          "• Dodaj mniej linków na raz\n"
                          "• Użyj `!paliwo` aby sprawdzić status quota",
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ **BŁĄD**\n{result['error']}\n\n"
                              f"✅ **Obsługiwane formaty:**\n"
                              + "\n".join(result.get('supported_formats', [])))
        
    except Exception as e:
        await ctx.send(f"❌ **BŁĄD SYSTEMU**\n{str(e)}") 