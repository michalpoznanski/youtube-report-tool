import os, json, datetime as dt
from typing import Dict, Any
from datetime import datetime, timedelta, date
from pathlib import Path

def base_dir():
    root = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume")
    path = os.path.join(root, "guest_analysis", "trends")
    os.makedirs(path, exist_ok=True)
    return path

def cat_dir(category: str):
    d = os.path.join(base_dir(), category.lower())
    os.makedirs(d, exist_ok=True)
    return d

def trends_path(category: str):
    return os.path.join(cat_dir(category), "video_trends.json")

def growth_path(category: str, report_date: str):
    return os.path.join(cat_dir(category), f"video_growth_{report_date}.json")

def stats_path(category: str, report_date: str):
    return os.path.join(cat_dir(category), f"stats_{report_date}.json")

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def growth_file_for_date(category: str, date_str: str) -> str:
    # istnieje już growth_path(category, date_str), użyj go
    return growth_path(category, date_str)

def previous_date_str(date_str: str) -> str | None:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (d - timedelta(days=1)).strftime("%Y-%m-%d")
    except Exception:
        return None

def load_growth_map_for_date(category: str, date_str: str) -> dict[str, dict]:
    """Zwraca mapę video_id -> record z growth.json dla wskazanej daty; puste gdy brak."""
    p = growth_file_for_date(category, date_str)
    if not p or not Path(p).exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f) or {}
    items = (data.get("growth") or [])
    return {x.get("video_id"): x for x in items if x.get("video_id")}

def list_growth_files(category: str):
    root = Path("/mnt/volume/guest_analysis/trends") / category
    if not root.exists():
        return []
    out = []
    for p in root.glob("video_growth_*.json"):  # Dopasowane do growth_path()
        try:
            # video_growth_YYYY-MM-DD.json
            date_str = p.stem.split("_", 2)[2]  # Split na 3 części
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            out.append((dt, p))
        except Exception:
            pass
    return sorted(out, key=lambda x: x[0])

def get_prev_growth_path(category: str, today_date: datetime):
    files = list_growth_files(category)
    prev = [p for (d, p) in files if d < today_date]
    return prev[-1][1] if prev else None

def report_dir() -> Path:
    """Katalog z raportami CSV"""
    return Path("/mnt/volume/reports")

def report_glob(category: str) -> str:
    """Wzorzec nazw plików CSV dla kategorii"""
    return f"report_{category.upper()}_*.csv"

# Stałe dla raportów CSV
REPORTS_DIR = "/mnt/volume/reports"

def list_report_files(category: str) -> list[tuple[datetime, Path]]:
    """Zwraca posortowaną listę (data, ścieżka) CSV dla kategorii"""
    root = Path(REPORTS_DIR)
    if not root.exists():
        return []
    
    out = []
    pattern = f"report_{category.upper()}_*.csv"
    for p in root.glob(pattern):
        try:
            # report_PODCAST_2025-08-09.csv -> 2025-08-09
            parts = p.stem.split("_", 2)
            if len(parts) < 3:
                continue
            date_str = parts[2]
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            out.append((dt, p))
        except Exception as e:
            # Log błędu dla debugowania
            print(f"Error parsing {p}: {e}")
            pass
    
    return sorted(out, key=lambda x: x[0])

def report_path_for_date(category: str, d: date) -> Path | None:
    """Znajdź dokładny plik CSV po dacie"""
    target_date = d.strftime("%Y-%m-%d")
    for dt, path in list_report_files(category):
        if dt.strftime("%Y-%m-%d") == target_date:
            return path
    return None

def prev_date(d: date) -> date:
    """Poprzedni dzień"""
    from datetime import timedelta
    return d - timedelta(days=1)
