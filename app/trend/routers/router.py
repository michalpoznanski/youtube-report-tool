import os, json, logging
from fastapi import APIRouter, Request
import logging
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..core.loader import load_latest
from ..core.dispatcher import analyze_category
from ..core.growth import update_growth
from ..core.store.trend_store import stats_path, growth_path, save_json, previous_date_str, load_growth_map_for_date
from ..core.stats import publish_hour_stats

log = logging.getLogger("trend")
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trend", tags=["trend"])

@router.api_route("/{category}/run", methods=["GET", "POST"])
def run(category: str):
    df, report_date = load_latest(category)
    if df is None: return JSONResponse({"error":"no report found"}, status_code=404)
    summary = analyze_category(category, df)
    glist = update_growth(category, df, report_date)
    
    # wzbogacenie o wczorajsze wartości i deltę
    if report_date:
        prev_str = previous_date_str(report_date)
        prev_map = load_growth_map_for_date(category, prev_str) if prev_str else {}
        
        for item in glist:
            vid = item.get("video_id")
            prev = prev_map.get(vid)
            if prev:
                vy = prev.get("views_today")
                try:
                    item["views_yesterday"] = int(vy) if vy is not None else None
                except Exception:
                    item["views_yesterday"] = None
                try:
                    if item.get("views_today") is not None and item.get("views_yesterday") is not None:
                        item["delta"] = int(item["views_today"]) - int(item["views_yesterday"])
                    else:
                        item["delta"] = None
                except Exception:
                    item["delta"] = None
            else:
                # brak wczorajszego odpowiednika
                item.setdefault("views_yesterday", None)
                item.setdefault("delta", None)
    
    # zapisz statystyki godzin
    st = publish_hour_stats(df)
    if report_date:
        save_json(stats_path(category, report_date), st)
        # zapisz wzbogacony growth
        save_json(growth_path(category, report_date), {"date": report_date, "growth": glist})
    
    return {"ok": True, "category": category, "report_date": report_date,
            "summary_count": len(summary.get("rank_top", [])), "growth_count": len(glist)}

@router.get("/{category}", response_class=HTMLResponse)
def page(category: str, request: Request):
    # HTML strona kategorii
    # ładowanie growth i stats jeśli istnieją (z najnowszego dnia – prosto: bierzemy plik z load_latest)
    df, report_date = load_latest(category)
    
    # a) Budowanie mapy metadata po video_id z df
    meta = {}
    try:
        for _, row in df.iterrows():
            vid = str(row.get("video_id", "")).strip()
            if not vid:
                continue
                
            short_heuristic = False
            # Sprawdź video_url zawiera '/shorts/'
            if 'video_url' in df.columns and row.get('video_url'):
                short_heuristic = short_heuristic or '/shorts/' in str(row.get('video_url', ''))
            # Sprawdź title zawiera '#shorts'
            if 'title' in df.columns and row.get('title'):
                short_heuristic = short_heuristic or '#shorts' in str(row.get('title', '')).lower()
            # Sprawdź duration_seconds < 60
            if 'duration_seconds' in df.columns and row.get('duration_seconds'):
                try:
                    duration = float(row.get('duration_seconds', 0))
                    short_heuristic = short_heuristic or duration < 60
                except (ValueError, TypeError):
                    pass
            
            meta[vid] = {
                'is_short': bool(short_heuristic),
                'channel_title': row.get('channel_title') if 'channel_title' in df.columns else None,
                'published_at': row.get('published_at') if 'published_at' in df.columns else None
            }
    except Exception as e:
        logger.warning('[TREND] Error building metadata: %s', e)
        meta = {}
    
    data_growth = {"growth":[]}
    data_stats = {}
    if report_date:
        try:
            gp = growth_path(category, report_date)
            if gp and Path(gp).exists():
                with open(gp, 'r', encoding='utf-8') as f:
                    data_growth = json.load(f)
            else:
                logger.warning('[TREND] growth file missing: %s', gp)
        except Exception as e:
            logger.exception('[TREND] growth read error: %s', e)
        try:
            sp = stats_path(category, report_date)
            if sp and sp and Path(sp).exists():
                with open(sp, 'r', encoding='utf-8') as f:
                    data_stats = json.load(f)
            else:
                logger.warning('[TREND] stats file missing: %s', sp)
        except Exception as e:
            logger.exception('[TREND] stats read error: %s', e)
    
    # b) Wzbogacenie growth o metadata
    growth_data = data_growth.get("growth", [])
    try:
        for item in growth_data:
            vid = item.get("video_id", "")
            if vid in meta:
                item["is_short"] = meta[vid]["is_short"]
                if meta[vid]["channel_title"]:
                    item["channel_title"] = meta[vid]["channel_title"]
                if meta[vid]["published_at"]:
                    item["published_at"] = meta[vid]["published_at"]
            else:
                item["is_short"] = False
    except Exception as e:
        logger.warning('[TREND] Error enriching growth data: %s', e)
    
    # Fallback: uzupełnij brakujące flagi is_short (gdy JSON jest starszy)
    def _safe_lower(s):
        try:
            return str(s).lower()
        except Exception:
            return ""

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

    def _detect_is_short_from_row(row: dict) -> bool:
        url = None
        for k in ("video_url", "url", "link", "watch_url"):
            if k in row and row[k]:
                url = _safe_lower(row[k])
                break
        title = _safe_lower(row.get("title"))
        duration_sec = None
        for k in ("duration_seconds", "duration_secs", "seconds"):
            if k in row and row[k] not in (None, ""):
                try:
                    duration_sec = int(float(row[k]))
                except Exception:
                    pass
                break
        if duration_sec is None:
            for k in ("duration", "length", "time"):
                if k in row and row[k]:
                    duration_sec = _parse_duration_to_seconds(row[k])
                    if duration_sec is not None:
                        break

        if url and "/shorts/" in url:
            return True
        if "#shorts" in title:
            return True
        if duration_sec is not None and duration_sec < 60:
            return True
        return False

    # uzupełnij brakujące flagi:
    try:
        for row in growth_data:
            if "is_short" not in row or row["is_short"] in (None, ""):
                row["is_short"] = _detect_is_short_from_row(row)
    except Exception as e:
        logger.warning('[TREND] Error in fallback is_short detection: %s', e)
    
    # c) Rozdzielenie na long_items i short_items
    try:
        long_items = [r for r in growth_data if not r.get("is_short", False)]
        short_items = [r for r in growth_data if r.get("is_short", False)]
    except Exception as e:
        logger.warning('[TREND] Error splitting items: %s', e)
        long_items = growth_data
        short_items = []
    
    # d) Opcjonalnie: dociągnięcie danych z dnia poprzedniego
    try:
        if report_date:
            # Oblicz prev_date = report_date - 1 dzień
            from datetime import datetime, timedelta
            try:
                prev_date = datetime.strptime(report_date, "%Y-%m-%d") - timedelta(days=1)
                prev_date_str = prev_date.strftime("%Y-%m-%d")
                
                # Sprawdź czy plik growth dla prev_date istnieje
                prev_gp = growth_path(category, prev_date_str)
                if prev_gp and Path(prev_gp).exists():
                    with open(prev_gp, 'r', encoding='utf-8') as f:
                        prev_data = json.load(f)
                        prev_map = {item.get("video_id"): item.get("views_today") for item in prev_data.get("growth", [])}
                        
                        # Wzbogacenie o wczorajsze wartości i deltę
                        for r in long_items + short_items:
                            if r.get("views_yesterday") is None:
                                r["views_yesterday"] = prev_map.get(r.get("video_id"))
                            # Oblicz delta jeśli obie wartości są liczbowe
                            if (r.get("views_today") is not None and 
                                r.get("views_yesterday") is not None):
                                try:
                                    r["delta"] = int(r["views_today"]) - int(r["views_yesterday"])
                                except (ValueError, TypeError):
                                    r["delta"] = None
            except Exception as e:
                logger.warning('[TREND] Error processing previous day data: %s', e)
    except Exception as e:
        logger.warning('[TREND] Error in previous day logic: %s', e)
    
    # e) Przygotowanie counts i sortowanie
    counts = {
        "long": len(long_items),
        "shorts": len(short_items),
        "all": len(growth_data)
    }
    
    # Sortowanie po views_today malejąco
    key_fn = lambda r: int(r.get("views_today") or 0)
    long_items = sorted(long_items, key=key_fn, reverse=True)[:50]
    short_items = sorted(short_items, key=key_fn, reverse=True)[:50]
    
    logger.info(f'[TREND] {category}: report_date={report_date}, counts={counts}')
    
    return templates.TemplateResponse(f"trend/{category.lower()}/dashboard.html",
                                     {"request": request, "category": category, "growth": data_growth, 
                                      "stats": data_stats, "report_date": report_date,
                                      "items": growth_data, "long_items": long_items, "short_items": short_items,
                                      "counts": counts})

@router.get("/{category}/growth")
def api_growth(category: str):
    df, report_date = load_latest(category)
    if not report_date: return {"growth": []}
    try:
        with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"growth": []}
