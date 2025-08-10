import os, json, logging
from fastapi import APIRouter, Request
import logging
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..core.loader import load_latest
from ..core.dispatcher import analyze_category
from ..core.growth import update_growth, _detect_is_short_from_csv_row
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
    
    # zbuduj mapa CSV: video_id -> {channel_title, duration_seconds, title, video_url}
    csv_map = {}
    if df is not None:
        # dopasuj do realnych nazw kolumn w Twoim CSV:
        # np. 'video_id','channel_title','duration_seconds','title','video_url'
        for _, row in df.iterrows():
            vid = str(row.get("video_id") or "").strip()
            if not vid: 
                continue
            csv_map[vid] = {
                "channel_title": row.get("channel_title"),
                "duration_seconds": row.get("duration_seconds"),
                "title": row.get("title"),
                "video_url": row.get("video_url"),
            }

    items = list(data_growth.get("growth") or [])
    # fallback uzupełniania
    for it in items:
        vid = it.get("video_id")
        csv_row = csv_map.get(vid) or {}
        if not it.get("channel"):
            it["channel"] = csv_row.get("channel_title") or "-"
        if it.get("is_short") in (None, ""):
            it["is_short"] = _detect_is_short_from_csv_row(csv_row)

    # rozdziel
    long_items = [x for x in items if not x.get("is_short")]
    short_items = [x for x in items if x.get("is_short")]

    # sortowanie po dzisiejszych
    long_items = sorted(long_items, key=lambda r: int(r.get("views_today") or 0), reverse=True)[:50]
    short_items = sorted(short_items, key=lambda r: int(r.get("views_today") or 0), reverse=True)[:50]

    logger.info(f'[TREND] {category}: report_date={report_date}, items={len(items)}, long={len(long_items)}, short={len(short_items)}')
    
    return templates.TemplateResponse(
        f"trend/{category.lower()}/dashboard.html",
        {
            "request": request,
            "category": category,
            "report_date": report_date,
            "items": items,
            "long_items": long_items,
            "short_items": short_items,
            "stats": data_stats or {},
        }
    )

@router.get("/{category}/growth")
def api_growth(category: str):
    df, report_date = load_latest(category)
    if not report_date: return {"growth": []}
    try:
        with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"growth": []}

@router.get("/{category}/_debug")
def debug(category: str):
    df, report_date = load_latest(category)
    out = {
        "report_date": str(report_date) if report_date else None,
        "csv_rows": int(df.shape[0]) if df is not None else 0,
    }
    try:
        with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
            g = json.load(f).get("growth", [])
        out["growth_count"] = len(g)
        # policz ile ma pola i_short True/False
        t = sum(1 for x in g if x.get("is_short") is True)
        f_ = sum(1 for x in g if x.get("is_short") is False)
        out["is_short_true"] = t
        out["is_short_false"] = f_
        out["has_views_yesterday"] = sum(1 for x in g if x.get("views_yesterday") is not None)
        out["sample"] = g[:3]
    except Exception as e:
        out["growth_error"] = str(e)
    return out
