import os, re, pandas as pd
import csv
from typing import Dict, Any, List
from datetime import datetime
from app.trend.core.store.trend_store import get_report_path, get_prev_date

def reports_dir():
    rd = os.environ.get("REPORTS_DIR")
    if rd: return rd
    base = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume")
    return os.path.join(base, "reports")

def find_latest(category: str):
    d = reports_dir()
    if not os.path.isdir(d): return None
    patt = re.compile(rf"report_{category.upper()}_\d{{4}}-\d{{2}}-\d{{2}}\.csv$")
    files = sorted([f for f in os.listdir(d) if patt.match(f)], reverse=True)
    if not files: return None
    return os.path.join(d, files[0])

def load_latest(category: str):
    p = find_latest(category)
    if not p: return None, None
    df = pd.read_csv(p)
    # raport_date z nazwy pliku
    report_date = os.path.basename(p).split("_")[-1].replace(".csv","")
    return df, report_date

def load_csv(category: str, date: datetime) -> List[Dict[str, Any]]:
    """Wczytaj CSV i znormalizuj pola"""
    csv_path = get_report_path(category, date)
    if not csv_path or not csv_path.exists():
        return []
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalizacja pól
                normalized = {
                    "video_id": str(row.get("video_id", "")).strip(),
                    "title": str(row.get("title", "")).strip(),
                    "channel": None,
                    "views": 0,
                    "is_short": None,
                    "duration_seconds": None
                }
                
                # Channel - preferuj 'channel', fallback 'channel_title'
                if row.get("channel"):
                    normalized["channel"] = str(row["channel"]).strip()
                elif row.get("channel_title"):
                    normalized["channel"] = str(row["channel_title"]).strip()
                
                # Views - preferuj 'views', fallback 'view_count'
                if row.get("views"):
                    try:
                        normalized["views"] = int(float(row["views"]))
                    except (ValueError, TypeError):
                        pass
                elif row.get("view_count"):
                    try:
                        normalized["views"] = int(float(row["view_count"]))
                    except (ValueError, TypeError):
                        pass
                
                # Duration
                if row.get("duration_seconds"):
                    try:
                        normalized["duration_seconds"] = int(float(row["duration_seconds"]))
                    except (ValueError, TypeError):
                        pass
                
                # is_short - jeśli jest w CSV
                if row.get("is_short"):
                    try:
                        normalized["is_short"] = bool(int(row["is_short"]))
                    except (ValueError, TypeError):
                        pass
                
                # Pomiń wiersze bez video_id
                if normalized["video_id"]:
                    rows.append(normalized)
    
    except Exception as e:
        print(f"Error loading CSV {csv_path}: {e}")
    
    return rows

def detect_is_short(row: Dict[str, Any]) -> bool:
    """Wykryj czy to short na podstawie dostępnych danych"""
    # 1. Jeśli is_short wiersza to bool → użyj
    if row.get("is_short") is not None:
        return bool(row["is_short"])
    
    # 2. Duration <= 61 sekund
    if row.get("duration_seconds") is not None:
        if row["duration_seconds"] <= 61:
            return True
    
    # 3. #shorts/shorts w tytule (casefold)
    title = str(row.get("title", "")).casefold()
    if "#shorts" in title or "shorts" in title:
        return True
    
    # 4. Default: False
    return False

def build_growth_from_csvs(category: str, today_date: datetime) -> Dict[str, Any]:
    """Zbuduj growth z CSV dla dzisiejszej i wczorajszej daty"""
    # Wczytaj dzisiejszy CSV
    today_rows = load_csv(category, today_date)
    if not today_rows:
        return {
            "date": today_date.strftime("%Y-%m-%d"),
            "source": "csv",
            "growth": []
        }
    
    # Znajdź wczorajszy CSV
    prev_date = get_prev_date(category, today_date)
    prev_rows = []
    if prev_date:
        prev_rows = load_csv(category, prev_date)
    
    # Mapy video_id -> views
    today_views = {row["video_id"]: row["views"] for row in today_rows}
    prev_views = {row["video_id"]: row["views"] for row in prev_rows}
    
    # Zbuduj growth
    growth = []
    for today_row in today_rows:
        video_id = today_row["video_id"]
        views_today = today_row["views"]
        views_yesterday = prev_views.get(video_id)
        
        # Oblicz delta
        delta = None
        if views_yesterday is not None:
            delta = views_today - views_yesterday
        
        # Wykryj is_short
        is_short = detect_is_short(today_row)
        
        growth_record = {
            "video_id": video_id,
            "title": today_row["title"],
            "channel": today_row["channel"] or "-",
            "views_today": views_today,
            "views_yesterday": views_yesterday,
            "delta": delta,
            "is_short": is_short
        }
        
        growth.append(growth_record)
    
    # Sortuj malejąco po views_today
    growth.sort(key=lambda x: x["views_today"], reverse=True)
    
    return {
        "date": today_date.strftime("%Y-%m-%d"),
        "source": "csv",
        "growth": growth
    }
