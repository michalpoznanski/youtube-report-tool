import os, json, logging
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.loader import load_latest
from ..core.dispatcher import analyze_category
from ..core.growth import update_growth
from ..core.store.trend_store import stats_path, growth_path, save_json
from ..core.stats import publish_hour_stats
from ..utils.report_loader import build_rolling_leaderboard
from datetime import datetime, timedelta

log = logging.getLogger("trend")
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/trend", tags=["trend"])

@router.post("/{category}/run")
def run(category: str):
    df, report_date = load_latest(category)
    if df is None: return JSONResponse({"error":"no report found"}, status_code=404)
    summary = analyze_category(category, df)
    glist = update_growth(category, df, report_date)
    # zapisz statystyki godzin
    st = publish_hour_stats(df)
    if report_date:
        save_json(stats_path(category, report_date), st)
    return {"ok": True, "category": category, "report_date": report_date,
            "summary_count": len(summary.get("rank_top", [])), "growth_count": len(glist)}

@router.get("/{category}", response_class=HTMLResponse)
def page(category: str, request: Request, mode: str = Query(None)):
    # HTML strona kategorii
    # ładowanie growth i stats jeśli istnieją (z najnowszego dnia – prosto: bierzemy plik z load_latest)
    df, report_date = load_latest(category)
    data_growth = {"growth":[]}
    data_stats = {}
    if report_date:
        try:
            with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
                data_growth = json.load(f)
        except Exception: pass
        try:
            with open(stats_path(category, report_date), "r", encoding="utf-8") as f:
                data_stats = json.load(f)
        except Exception: pass
    return templates.TemplateResponse(f"trend/{category.lower()}/dashboard.html",
                                     {"request": request, "category": category, "growth": data_growth, "stats": data_stats, "report_date": report_date})

@router.get("/{category}/top", response_class=HTMLResponse)
def top_ranking(category: str, request: Request, days: int = Query(3, ge=1, le=30), k: int = Query(15, ge=1, le=100)):
    """Endpoint dla rankingów TOP K z N dni"""
    try:
        # Pobierz dzisiejszą datę jako end_date
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Pobierz ranking
        leaderboard = build_rolling_leaderboard(category, end_date, days, k)
        
        # Sprawdź czy są dane
        if not leaderboard.get("longs") and not leaderboard.get("shorts"):
            # Spróbuj z wczorajszą datą
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            leaderboard = build_rolling_leaderboard(category, yesterday, days, k)
        
        return templates.TemplateResponse(f"trend/{category.lower()}/top.html",
                                        {"request": request, "category": category, "leaderboard": leaderboard})
    except Exception as e:
        log.error(f"Error in top_ranking for category {category}: {e}")
        return templates.TemplateResponse(f"trend/{category.lower()}/top.html",
                                        {"request": request, "category": category, "leaderboard": None, "error": str(e)})

@router.get("/{category}/growth")
def api_growth(category: str):
    df, report_date = load_latest(category)
    if not report_date: return {"growth": []}
    try:
        with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"growth": []}
