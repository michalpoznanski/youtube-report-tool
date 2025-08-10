import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, List
from .store.trend_store import load_json, save_json, trends_path, growth_path, get_prev_growth_path

def _parse_duration_to_seconds(s):
    if not s: return None
    parts = str(s).split(":")
    try:
        parts = [int(p) for p in parts]
    except Exception:
        return None
    if len(parts) == 3:
        h, m, sec = parts; return h*3600 + m*60 + sec
    if len(parts) == 2:
        m, sec = parts; return m*60 + sec
    if len(parts) == 1:
        return parts[0]
    return None

def _detect_is_short_from_csv_row(row: Dict[str, Any]) -> bool:
    title = (row.get("title") or "").lower()
    url = (row.get("video_url") or "").lower()
    dur = row.get("duration_seconds") or row.get("duration")
    sec = None
    try:
        sec = int(dur) if str(dur).isdigit() else _parse_duration_to_seconds(dur)
    except Exception:
        pass
    if "/shorts/" in url or "#shorts" in title: 
        return True
    if sec is not None and sec < 60:
        return True
    return False

def build_and_save_growth(category, report_date, today_rows, today_csv_map, out_path):
    prev_path = get_prev_growth_path(category, report_date)
    prev_views = {}
    if prev_path:
        try:
            with open(prev_path, "r", encoding="utf-8") as f:
                prev = json.load(f).get("growth", [])
            prev_views = {r["video_id"]: int(r.get("views_today") or 0) for r in prev if r.get("video_id")}
        except Exception:
            prev_views = {}
    result = []
    for r in today_rows:
        vid = r.get("video_id")
        csv_row = today_csv_map.get(vid) or {}
        chan = csv_row.get("channel_title") or "-"
        is_short = r.get("is_short")
        if is_short in (None, ""):
            is_short = _detect_is_short_from_csv_row(csv_row)
        views_today = int(r.get("views_today") or 0)
        views_yesterday = prev_views.get(vid)
        delta = views_today - views_yesterday if isinstance(views_yesterday, int) else None
        out = dict(r)
        out["channel"] = channel
        out["is_short"] = bool(is_short)
        out["views_yesterday"] = views_yesterday
        out["delta"] = delta
        result.append(out)
    payload = {"date": report_date.strftime("%Y-%m-%d"), "growth": result}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

def update_growth(category: str, df: pd.DataFrame, report_date: str):
    trends = load_json(trends_path(category))
    # Zapis historii views per Video_ID
    for _, r in df.iterrows():
        vid = str(r.get("Video_ID","")).strip()
        if not vid: continue
        title = str(r.get("Title",""))
        views = int(pd.to_numeric(r.get("View_Count",0), errors="coerce") or 0)
        entry = trends.get(vid, {"title": title, "history": []})
        # unikamy duplikatu dla danej daty
        if not any(h.get("date")==report_date for h in entry["history"]):
            entry["history"].append({"date": report_date, "views": views})
            # sort rosnąco po dacie
            entry["history"] = sorted(entry["history"], key=lambda x: x["date"])
        entry["title"] = title or entry.get("title","")
        trends[vid] = entry
    save_json(trends_path(category), trends)

    # Oblicz delta lista na dziś
    growth_list = []
    for vid, entry in trends.items():
        hist = entry.get("history", [])
        if not hist: continue
        today = next((h for h in hist if h["date"]==report_date), None)
        if not today: continue
        # szukaj poprzedniego pomiaru
        prev_items = [h for h in hist if h["date"]<report_date]
        prev = prev_items[-1] if prev_items else None
        
        growth_list.append({
            "video_id": vid,
            "title": entry.get("title",""),
            "views_today": today["views"],
            "views_yesterday": prev["views"] if prev else None,
            "delta": (today["views"] - prev["views"]) if prev else None
        })
    
    # Stwórz mapę CSV dla wzbogacenia danych
    today_csv_map = {}
    for _, r in df.iterrows():
        vid = str(r.get("Video_ID","")).strip()
        if vid:
            today_csv_map[vid] = r.to_dict()
    
    # Użyj nowej funkcji do wzbogacenia i zapisu
    report_date_dt = datetime.strptime(report_date, "%Y-%m-%d")
    out_path = growth_path(category, report_date)
    build_and_save_growth(category, report_date_dt, growth_list, today_csv_map, out_path)
    
    # Wczytaj wzbogacone dane do zwrotu
    with open(out_path, "r", encoding="utf-8") as f:
        enriched_data = json.load(f)
    
    return enriched_data.get("growth", [])

def save_growth(category: str, date: datetime, data: Dict[str, Any]) -> None:
    """Zapisz growth JSON do pliku"""
    try:
        out_path = growth_path(category, date.strftime("%Y-%m-%d"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # logger.info(f'[GROWTH] Saved {category} growth for {date.strftime("%Y-%m-%d")}: {len(data.get("growth", []))} items') # Original code had this line commented out
    except Exception as e:
        # logger.error(f'[GROWTH] Error saving {category} growth: {e}') # Original code had this line commented out
        raise
