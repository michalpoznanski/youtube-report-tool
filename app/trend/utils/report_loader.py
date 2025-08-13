# app/trend/utils/report_loader.py

import csv
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

REPORTS_DIR = "/mnt/volume/reports"

def load_daily_report(category: str, date: str) -> List[Dict[str, Any]]:
    """
    Wczytuje raport dzienny dla danej kategorii i daty, normalizuje kolumny,
    wylicza pole is_short oraz zwraca listę rekordów jako słowniki.
    """
    category_upper = category.upper()
    filename = f"report_{category_upper}_{date}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    if not os.path.isfile(filepath):
        # Zwracamy pustą listę, jeśli plik nie istnieje
        return []

    data: List[Dict[str, Any]] = []
    with open(filepath, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Normalizacja kluczy: małe litery, usunięcie spacji
            normalized = {k.strip().lower(): v for k, v in row.items()}

            # Konwersja liczby wyświetleń do int – różne możliwe nazwy kolumn
            views = None
            for key in ["views_today", "view_count", "views", "view_count"]:
                if key in normalized:
                    try:
                        views = int(normalized.pop(key))
                    except (ValueError, TypeError):
                        views = 0
                    break
            normalized["views_today"] = views if views is not None else 0

            # Konwersja czasu trwania na sekundy
            duration = None
            for key in ["duration_seconds", "duration"]:
                if key in normalized:
                    try:
                        duration_str = normalized.pop(key)
                        # Obsługa formatu ISO 8601 (PT5M30S)
                        if isinstance(duration_str, str) and duration_str.startswith('PT'):
                            # Parsowanie PT5M30S -> 5*60 + 30 = 330 sekund
                            duration_str = duration_str[2:]  # Usuń 'PT'
                            minutes = 0
                            seconds = 0
                            
                            # Znajdź minuty (M)
                            if 'M' in duration_str:
                                parts = duration_str.split('M')
                                minutes = int(parts[0])
                                duration_str = parts[1] if len(parts) > 1 else ''
                            
                            # Znajdź sekundy (S)
                            if 'S' in duration_str:
                                seconds = int(duration_str.replace('S', ''))
                            
                            duration = minutes * 60 + seconds
                        else:
                            duration = int(float(duration_str))
                    except (ValueError, TypeError):
                        duration = None
                    break
            normalized["duration_seconds"] = duration

            # Przekopiuj inne istotne pola (title, channel, tags, description, video_id)
            # Jeśli któreś z nich nie istnieje w pliku, ustaw pusty string
            for field in ["title", "channel", "tags", "description", "video_id"]:
                normalized[field] = normalized.get(field, "") or ""

            # Detekcja czy film jest short
            text_concat = f"{normalized['title']} {normalized['tags']} {normalized['description']}".lower()
            is_short = False
            if duration is not None and duration < 62:
                is_short = True
            elif "#short" in text_concat or "#shorts" in text_concat:
                is_short = True
            normalized["is_short"] = is_short

            # Upewnij się, że zwracamy klucz video_id, title, channel, views_today, duration_seconds, is_short
            record = {
                "video_id": normalized["video_id"],
                "title": normalized["title"],
                "channel": normalized["channel"],
                "views_today": normalized["views_today"],
                "duration_seconds": normalized["duration_seconds"],
                "is_short": normalized["is_short"],
                # Zachowaj oryginalne pola dla dalszych operacji, jeśli będą potrzebne
                "tags": normalized["tags"],
                "description": normalized["description"],
            }

            data.append(record)

    return data


def build_daily_growth(category: str, date: str) -> List[Dict[str, Any]]:
    """
    Buduje listę rekordów z informacją o wczorajszych wyświetleniach i różnicy (delta).
    
    Args:
        category (str): Kategoria, np. "podcast".
        date (str): Data w formacie YYYY-MM-DD.

    Returns:
        List[Dict[str, Any]]: Lista rekordów z kluczami views_yesterday i delta.
    """
    # Wczytaj dane z bieżącego dnia
    today_records = load_daily_report(category, date)

    # Ustal datę poprzedniego dnia
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    prev_date_obj = date_obj - timedelta(days=1)
    prev_date_str = prev_date_obj.isoformat()

    # Wczytaj dane z poprzedniego dnia
    prev_records = load_daily_report(category, prev_date_str)

    # Zmapuj wyświetlenia z poprzedniego dnia po video_id
    prev_views_map = {rec["video_id"]: rec["views_today"] for rec in prev_records}

    growth_records: List[Dict[str, Any]] = []
    for record in today_records:
        vid = record.get("video_id")
        current_views = record.get("views_today", 0)
        yesterday_views = prev_views_map.get(vid, 0)
        delta = current_views - yesterday_views

        # Utwórz kopię rekordu, aby nie modyfikować oryginalnych danych
        growth_record = record.copy()
        growth_record["views_yesterday"] = yesterday_views
        growth_record["delta"] = delta

        growth_records.append(growth_record)

    return growth_records
