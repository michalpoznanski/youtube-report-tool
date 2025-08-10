import pandas as pd
from .store.trend_store import load_json, save_json, trends_path, growth_path

def _parse_duration_to_seconds(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    parts = s.split(":")
    try:
        parts = [int(p) for p in parts]
    except Exception:
        return None
    if len(parts) == 3:  # H:MM:SS
        h, m, sec = parts
        return h*3600 + m*60 + sec
    if len(parts) == 2:  # MM:SS
        m, sec = parts
        return m*60 + sec
    if len(parts) == 1:  # SS
        return parts[0]
    return None

def _detect_is_short(record: dict) -> bool:
    # spróbuj znaleźć link kolumny
    url = None
    for k in ("video_url", "url", "link", "watch_url", "Video_URL"):
        if k in record and record[k]:
            url = str(record[k]).lower()
            break

    title = str(record.get("title", "")).lower()
    duration_sec = None
    # preferuj już policzone sekundy
    for k in ("duration_seconds", "duration_secs", "seconds", "Duration_Seconds"):
        if k in record and record[k] not in (None, ""):
            try:
                duration_sec = int(float(record[k]))
            except Exception:
                pass
            break
    if duration_sec is None:
        # spróbuj sparsować MM:SS / H:MM:SS
        for k in ("duration", "length", "time", "Duration"):
            if k in record and record[k]:
                duration_sec = _parse_duration_to_seconds(record[k])
                if duration_sec is not None:
                    break

    # HEURYSTYKA
    if url and "/shorts/" in url:
        return True
    if "#shorts" in title:
        return True
    if duration_sec is not None and duration_sec < 60:
        return True
    return False

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
        # Pobierz oryginalne dane z CSV dla tego video_id
        original_record = None
        for _, r in df.iterrows():
            if str(r.get("Video_ID", "")).strip() == vid:
                original_record = r.to_dict()
                break
        
        # Użyj solidnej heurystyki do wykrywania Shorts
        is_short = False
        if original_record:
            is_short = _detect_is_short(original_record)
        
        growth_list.append({
            "video_id": vid,
            "title": entry.get("title",""),
            "views_today": today["views"],
            "views_yesterday": prev["views"] if prev else None,
            "delta": (today["views"] - prev["views"]) if prev else None,
            "is_short": is_short
        })
    # sort malejąco po delta (None na dół)
    growth_list = sorted(growth_list, key=lambda x: (-1_000_000_000 if x["delta"] is None else -x["delta"], -x["views_today"]))
    save_json(growth_path(category, report_date), {"date": report_date, "growth": growth_list})
    return growth_list
