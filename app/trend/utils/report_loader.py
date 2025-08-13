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

            # Konwersja czasu trwania na sekundy z różnych kolumn
            duration_seconds = None
            # Pobierz dowolną kolumnę z czasem trwania
            iso_dur = (
                normalized.get("duration_seconds")
                or normalized.get("duration")
                or normalized.get("durationiso")
                or normalized.get("duration_iso")
                or normalized.get("duration")
            )
            
            if iso_dur:
                try:
                    if isinstance(iso_dur, str) and iso_dur.startswith('PT'):
                        # Parsowanie ISO 8601: PT1H33M7S, PT45S, PT1M5S
                        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
                        match = re.match(pattern, iso_dur)
                        if match:
                            hours = int(match.group(1) or 0)
                            minutes = int(match.group(2) or 0)
                            seconds = int(match.group(3) or 0)
                            duration_seconds = hours * 3600 + minutes * 60 + seconds
                    else:
                        duration_seconds = int(float(iso_dur))
                except (ValueError, TypeError):
                    duration_seconds = None
                
                # Usuń wszystkie kolumny z czasem trwania
                for key in ["duration_seconds", "duration", "durationiso", "duration_iso"]:
                    normalized.pop(key, None)
            
            normalized["duration_seconds"] = duration_seconds

            # Przekopiuj inne istotne pola (title, channel, tags, description, video_id)
            # Jeśli któreś z nich nie istnieje w pliku, ustaw pusty string
            for field in ["title", "channel", "tags", "description", "video_id"]:
                normalized[field] = normalized.get(field, "") or ""

            # Ustal, czy film jest short na podstawie video_type
            video_type_value = normalized.get("video_type", "") or ""
            video_type_value = video_type_value.strip().lower()

            # Rozpoznaj wszystkie warianty słów 'short' i 'long'
            if "short" in video_type_value:
                is_short = True
            elif "long" in video_type_value:
                is_short = False
            else:
                # fallback heurystyka – czas < 62 sekund lub tag #short/#shorts
                text_concat = f"{normalized['title']} {normalized['tags']} {normalized['description']}".lower()
                is_short = (
                    normalized.get("duration_seconds") is not None
                    and normalized["duration_seconds"] < 62
                ) or ("#short" in text_concat or "#shorts" in text_concat)
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

    # Oblicz dodatkowe metryki: percent_growth i potential
    max_delta = max((rec["delta"] for rec in growth_records if rec["delta"] > 0), default=0)
    
    for rec in growth_records:
        # Procentowy wzrost
        if rec["views_yesterday"] > 0:
            rec["percent_growth"] = round(((rec["views_today"] - rec["views_yesterday"]) / rec["views_yesterday"]) * 100, 2)
        else:
            rec["percent_growth"] = None
        
        # Potencjał 0-100
        if max_delta > 0 and rec["delta"] > 0:
            rec["potential"] = round((rec["delta"] / max_delta) * 100)
        else:
            rec["potential"] = 0

    return growth_records
