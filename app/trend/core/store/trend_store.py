import os, json, datetime as dt
from typing import Dict, Any

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
