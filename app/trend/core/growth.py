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

def detect_is_short(item: Dict[str, Any]) -> bool:
    """Heurystyka detekcji shorts"""
    # Duration < 62 sekund
    if item.get("duration_seconds") is not None:
        if item["duration_seconds"] < 62:
            return True
    
    # #short/#shorts w title/tags/description (case-insensitive)
    title = str(item.get("title", "")).lower()
    tags = str(item.get("tags", "")).lower()
    description = str(item.get("description", "")).lower()
    
    if "#short" in title or "#shorts" in title:
        return True
    if "short" in tags or "shorts" in tags:
        return True
    if "short" in description or "shorts" in description:
        return True
    
    return False

def build_growth_from_csv(category: str, d: date) -> Dict[str, Any]:
    """Zbuduj growth z CSV dla dzisiejszej i wczorajszej daty"""
    from app.trend.core.csv_loader import read_csv_for_date
    from app.trend.core.store.trend_store import prev_date
    
    # Wczytaj dzisiejszy CSV
    today = read_csv_for_date(category, d)
    if not today:
        return {
            "date": d.isoformat(),
            "growth": []
        }
    
    # Wczytaj wczorajszy CSV
    yest = read_csv_for_date(category, prev_date(d))
    yest_map = {row["video_id"]: row["views"] for row in yest}
    
    # Zbuduj growth
    growth_items = []
    for today_row in today:
        video_id = today_row["video_id"]
        views_today = int(today_row["views"])
        views_yesterday = yest_map.get(video_id)
        
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
        
        growth_items.append(growth_record)
    
    # Sortuj malejąco po views_today
    growth_items.sort(key=lambda x: x["views_today"], reverse=True)
    
    return {
        "date": d.isoformat(),
        "growth": growth_items
    }

def save_growth_and_stats(category: str, d: datetime, payload: Dict[str, Any]) -> None:
    """Zapisz growth JSON i policz stats"""
    try:
        # Zapisz growth
        out_path = growth_path(category, d.strftime("%Y-%m-%d"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        # Policz stats
        growth_items = payload.get("growth", [])
        long_count = sum(1 for x in growth_items if not x.get("is_short", False))
        short_count = sum(1 for x in growth_items if x.get("is_short", False))
        
        # Top godziny publikacji (jeśli mamy published_at)
        long_hours = {}
        short_hours = {}
        
        for item in growth_items:
            published_at = item.get("published_at")
            if published_at:
                try:
                    # Próbuj sparsować różne formaty daty
                    from datetime import datetime
                    if "T" in published_at:
                        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    else:
                        dt = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
                    
                    hour = dt.hour
                    if item.get("is_short", False):
                        short_hours[hour] = short_hours.get(hour, 0) + 1
                    else:
                        long_hours[hour] = long_hours.get(hour, 0) + 1
                except Exception:
                    pass
        
        # Top godziny
        top_long_hour = max(long_hours.items(), key=lambda x: x[1])[0] if long_hours else None
        top_short_hour = max(short_hours.items(), key=lambda x: x[1])[0] if short_hours else None
        
        stats = {
            "date": d.isoformat(),
            "total_items": len(growth_items),
            "long_count": long_count,
            "short_count": short_count,
            "top_long_hour": top_long_hour,
            "top_short_hour": top_short_hour
        }
        
        # Zapisz stats
        stats_path_file = stats_path(category, d.strftime("%Y-%m-%d"))
        with open(stats_path_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f'[TREND/CSV] Saved {category} growth for {d.isoformat()}: {len(growth_items)} items (long: {long_count}, short: {short_count})')
        
    except Exception as e:
        logger.error(f'[TREND/CSV] Error saving {category} growth/stats: {e}')
        raise

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
