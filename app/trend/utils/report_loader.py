# app/trend/utils/report_loader.py

import csv
import os
import re
import glob
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_reports_dir():
    """Zwraca ścieżkę do katalogu raportów z fallbackiem"""
    import os
    # Sprawdź lokalny katalog reports
    local_reports = "./hook-boost-web/reports"
    if os.path.exists(local_reports):
        return local_reports
    # Fallback do domyślnego
    return "/mnt/volume/reports"

def load_daily_report(category: str, date: str) -> List[Dict[str, Any]]:
    """
    Wczytuje raport dzienny dla danej kategorii i daty, normalizuje kolumny,
    wylicza pole is_short oraz zwraca listę rekordów jako słowniki.
    """
    category_upper = category.upper()
    filename = f"report_{category_upper}_{date}.csv"
    reports_dir = get_reports_dir()
    filepath = os.path.join(reports_dir, filename)
    
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
            
            # Mapuj Channel_Name → channel
            if "channel_name" in normalized:
                # Użyj channel_name jako channel
                normalized["channel"] = normalized.pop("channel_name")

            # Ustal, czy film jest short
            video_type_value = normalized.get("video_type", "") or ""
            video_type_value = video_type_value.strip().lower()
            duration_seconds = normalized.get("duration_seconds")

            # 1. Reguła długości: jeśli mamy czas trwania i jest krótszy niż 3 minuty, traktujemy jako Short
            if duration_seconds is not None and duration_seconds < 180:
                is_short = True
            # 2. Wykorzystanie video_type, gdy czas trwania nie kwalifikuje się do krótkiej formy
            elif "short" in video_type_value:
                is_short = True
            elif "long" in video_type_value:
                is_short = False
            else:
                # 3. Fallback heurystyka: czas < 62 sekund lub tag #short/#shorts w tytule/tagach/opisie
                text_concat = f"{normalized['title']} {normalized['tags']} {normalized['description']}".lower()
                is_short = (
                    duration_seconds is not None and duration_seconds < 62
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


def _available_dates_for_category(category: str, reports_dir: str = None) -> List[str]:
    if reports_dir is None:
        # Fallback do lokalnego katalogu reports
        import os
        local_reports = "./hook-boost-web/reports"
        if os.path.exists(local_reports):
            reports_dir = local_reports
        else:
            reports_dir = "/mnt/volume/reports"
    
    pattern = os.path.join(reports_dir, f"report_{category.upper()}_*.csv")
    files = sorted(glob.glob(pattern))
    dates = []
    for f in files:
        try:
            d = os.path.basename(f).split("_")[-1].replace(".csv","")
            datetime.strptime(d, "%Y-%m-%d")
            dates.append(d)
        except Exception:
            continue
    return dates


def load_reports_range(category: str, end_date: str, days: int) -> List[Dict[str, Any]]:
    """
    Wczytuje rekordy dla zakresu dat [end_date - (days-1) .. end_date].
    Zwraca listę elementów: {"date": "...", "records": [...]}
    """
    out: List[Dict[str, Any]] = []
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    for i in range(days-1, -1, -1):
        d = (end - timedelta(days=i)).isoformat()
        recs = load_daily_report(category, d)  # używamy obecnej logiki z 3-min progiem
        out.append({"date": d, "records": recs})
        logging.info(f"[ROLLING] Loaded {len(recs)} for {category=} {d=}")
    return out


def build_rolling_leaderboard(category: str, end_date: str, days: int = 3, top_k: int = 15):
    """Tworzy leaderboard na podstawie MAKS views_today w oknie N dni."""
    window = load_reports_range(category, end_date, days)
    per_video: Dict[str, Dict[str, Any]] = {}

    for day in window:
        d = day["date"]
        for r in day["records"]:
            vid = r.get("video_id")
            if not vid:
                continue
            entry = per_video.setdefault(vid, {
                "video_id": vid,
                "title": r.get("title"),
                "channel": r.get("channel"),
                "is_short": r.get("is_short"),
                "duration_seconds": r.get("duration_seconds"),
                "history": [],         # [(date, views_today)]
                "best_views": 0,
                "best_date": None,
                "last_views": 0,       # views_today w end_date
            })
            v = int(r.get("views_today", 0) or 0)
            entry["history"].append((d, v))
            if v > entry["best_views"]:
                entry["best_views"] = v
                entry["best_date"] = d
            if d == end_date:
                entry["last_views"] = v

    # podział i sortowanie
    longs = [e for e in per_video.values() if not e.get("is_short")]
    shorts = [e for e in per_video.values() if e.get("is_short")]

    # Skala potencjału 0–100 wg best_views w grupie
    def _attach_potential(items):
        max_best = max((x["best_views"] for x in items), default=0)
        for x in items:
            if max_best > 0 and x["best_views"] > 0:
                x["potential"] = round((x["best_views"] / max_best) * 100)
            else:
                x["potential"] = 0
        # sort po potencjale malejąco
        items.sort(key=lambda z: z["potential"], reverse=True)
        return items

    longs = _attach_potential(longs)[:top_k]
    shorts = _attach_potential(shorts)[:top_k]

    return {
        "end_date": end_date,
        "days": days,
        "top_k": top_k,
        "longs": longs,
        "shorts": shorts,
    }
