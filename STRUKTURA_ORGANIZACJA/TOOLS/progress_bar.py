#!/usr/bin/env python3
"""
Progress Bar System dla Discord
Tworzy i aktualizuje pasek postępu w czasie rzeczywistym
"""

import discord
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class DiscordProgressBar:
    def __init__(self, ctx, title: str = "Przetwarzanie...", description: str = "", is_offline: bool = False):
        self.ctx = ctx
        self.title = title
        self.description = description
        self.is_offline = is_offline  # Czy to analiza offline (0 quota)
        self.message = None
        self.current_step = 0
        self.total_steps = 100
        self.step_names = {}
        self.start_time = datetime.now(timezone.utc)
        
    async def create_progress_bar(self) -> discord.Message:
        """Tworzy początkowy pasek postępu"""
        embed = self._create_progress_embed()
        self.message = await self.ctx.send(embed=embed)
        return self.message
    
    def _create_progress_embed(self) -> discord.Embed:
        """Tworzy embed z paskiem postępu"""
        percentage = (self.current_step / self.total_steps) * 100
        
        # Twórz pasek postępu
        bar_length = 20
        filled_length = int((self.current_step / self.total_steps) * bar_length)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Oblicz czas
        elapsed = datetime.now(timezone.utc) - self.start_time
        elapsed_str = f"{elapsed.seconds}s"
        
        # Szacuj pozostały czas
        if self.current_step > 0:
            estimated_total = (elapsed.total_seconds() / self.current_step) * self.total_steps
            remaining = estimated_total - elapsed.total_seconds()
            remaining_str = f"{int(remaining)}s" if remaining > 0 else "0s"
        else:
            remaining_str = "???"
        
        embed = discord.Embed(
            title=f"🔄 {self.title}",
            description=self.description,
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Pasek postępu
        embed.add_field(
            name="📊 **Postęp**",
            value=f"```{bar} {percentage:.1f}%```",
            inline=False
        )
        
        # Szczegóły
        embed.add_field(
            name="⏱️ **Czas**",
            value=f"• **Uplynęło:** {elapsed_str}\n• **Pozostało:** {remaining_str}",
            inline=True
        )
        
        embed.add_field(
            name="📈 **Status**",
            value=f"• **Krok:** {self.current_step}/{self.total_steps}\n• **Szacowany koszt:** {self._estimate_quota_cost()} quota",
            inline=True
        )
        
        # Aktualny krok
        if self.current_step in self.step_names:
            embed.add_field(
                name="🎯 **Aktualnie**",
                value=f"```{self.step_names[self.current_step]}```",
                inline=False
            )
        
        return embed
    
    def _estimate_quota_cost(self) -> str:
        """Szacuje koszt quota na podstawie postępu"""
        if self.is_offline:
            return "0 quota (offline)"
        
        if self.current_step == 0:
            return "???"
        
        # Szacunek na podstawie kroku (tylko dla operacji online)
        if self.current_step < 20:
            return "~50-100"
        elif self.current_step < 50:
            return "~100-200"
        elif self.current_step < 80:
            return "~200-300"
        else:
            return "~300-500"
    
    async def update_progress(self, step: int, step_name: str = None, description: str = None, sub_progress: float = None):
        """Aktualizuje pasek postępu z opcjonalnym pod-progressem"""
        self.current_step = min(step, self.total_steps)
        
        if step_name:
            self.step_names[step] = step_name
        
        if description:
            self.description = description
        
        # Dodaj pod-progress do nazwy kroku
        if sub_progress is not None and step in self.step_names:
            self.step_names[step] = f"{self.step_names[step]} ({sub_progress:.1f}%)"
        
        if self.message:
            try:
                embed = self._create_progress_embed()
                await self.message.edit(embed=embed)
            except discord.NotFound:
                # Wiadomość została usunięta
                pass
            except Exception as e:
                print(f"Błąd aktualizacji progress bar: {e}")
    
    async def update_sub_progress(self, current: int, total: int, step_name: str = None):
        """Aktualizuje pod-progress w ramach aktualnego kroku"""
        if total > 0:
            sub_progress = (current / total) * 100
            await self.update_progress(self.current_step, step_name, sub_progress=sub_progress)
    
    async def set_total_steps(self, total: int):
        """Ustawia całkowitą liczbę kroków"""
        self.total_steps = total
    
    async def add_step(self, step_name: str):
        """Dodaje krok do listy"""
        self.step_names[len(self.step_names)] = step_name
    
    async def complete(self, final_message: str = "✅ Zakończono!", color: int = 0x00ff00):
        """Oznacza proces jako zakończony"""
        if not self.message:
            return
        
        elapsed = datetime.now(timezone.utc) - self.start_time
        
        embed = discord.Embed(
            title=f"✅ {self.title}",
            description=final_message,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="⏱️ **Czas wykonania**",
            value=f"**{elapsed.seconds} sekund**",
            inline=True
        )
        
        embed.add_field(
            name="📊 **Postęp**",
            value=f"**100%** - Wszystkie kroki ukończone",
            inline=True
        )
        
        try:
            await self.message.edit(embed=embed)
        except:
            pass
    
    async def error(self, error_message: str):
        """Oznacza proces jako błąd"""
        if not self.message:
            return
        
        embed = discord.Embed(
            title=f"❌ {self.title}",
            description=f"**Błąd:** {error_message}",
            color=0xff0000,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🔧 **Rozwiązanie**",
            value="• Sprawdź połączenie z internetem\n• Sprawdź czy API key jest poprawny\n• Spróbuj ponownie za chwilę",
            inline=False
        )
        
        try:
            await self.message.edit(embed=embed)
        except:
            pass

class DataCollectionProgress:
    """Specjalizowany progress bar dla zbierania danych"""
    
    def __init__(self, ctx, num_channels: int, days: int):
        self.ctx = ctx
        self.num_channels = num_channels
        self.days = days
        self.progress_bar = None
        
        # Kroki dla zbierania danych
        self.steps = [
            "Sprawdzanie bezpieczeństwa",
            "Inicjalizacja YouTube API",
            "Pobieranie listy kanałów",
            "Analiza kanałów",
            "Pobieranie filmów",
            "Przetwarzanie metadanych",
            "Wyciąganie nazwisk",
            "Zapisywanie do CSV",
            "Finalizacja"
        ]
    
    async def start(self):
        """Rozpoczyna proces z progress barem"""
        self.progress_bar = DiscordProgressBar(
            self.ctx,
            title="ZBIERANIE DANYCH",
            description=f"Zbieram dane z **{self.num_channels} kanałów** z ostatnich **{self.days} dni**"
        )
        
        await self.progress_bar.set_total_steps(len(self.steps))
        
        # Dodaj kroki
        for i, step in enumerate(self.steps):
            await self.progress_bar.add_step(step)
        
        return await self.progress_bar.create_progress_bar()
    
    async def update_step(self, step_index: int, custom_message: str = None):
        """Aktualizuje konkretny krok"""
        if self.progress_bar:
            step_name = custom_message or self.steps[step_index]
            await self.progress_bar.update_progress(step_index + 1, step_name)
    
    async def complete_success(self, file_name: str, file_size: float):
        """Oznacza sukces zbierania danych"""
        if self.progress_bar:
            final_message = f"✅ Dane zebrane pomyślnie!\n📁 **Plik:** `{file_name}`\n📊 **Rozmiar:** {file_size:.1f} KB"
            await self.progress_bar.complete(final_message, 0x00ff00)
    
    async def complete_error(self, error: str):
        """Oznacza błąd zbierania danych"""
        if self.progress_bar:
            await self.progress_bar.error(error)

# Przykład użycia w data_collector.py:
"""
async def collect_data_with_progress(ctx, days: int = 7):
    channels = get_all_channels()
    progress = DataCollectionProgress(ctx, len(channels), days)
    
    await progress.start()
    
    try:
        # Krok 1: Sprawdzanie bezpieczeństwa
        await progress.update_step(0)
        await asyncio.sleep(1)
        
        # Krok 2: Inicjalizacja API
        await progress.update_step(1)
        # ... kod inicjalizacji
        
        # Krok 3: Pobieranie kanałów
        await progress.update_step(2)
        # ... kod pobierania
        
        # ... kolejne kroki
        
        # Sukces
        await progress.complete_success("youtube_data_2025-07-24.csv", 1024.5)
        
    except Exception as e:
        await progress.complete_error(str(e))
""" 