import pandas as pd
from .store.trend_store import load_json, save_json, trends_path, growth_path

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
    # sort malejąco po delta (None na dół)
    growth_list = sorted(growth_list, key=lambda x: (-1_000_000_000 if x["delta"] is None else -x["delta"], -x["views_today"]))
    save_json(growth_path(category, report_date), {"date": report_date, "growth": growth_list})
    return growth_list
