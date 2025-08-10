import os, json, logging
from fastapi import APIRouter, Request
import logging
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.loader import load_latest
from ..core.dispatcher import analyze_category
from ..core.growth import update_growth
from ..core.store.trend_store import stats_path, growth_path, save_json
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
    # zapisz statystyki godzin
    st = publish_hour_stats(df)
    if report_date:
        save_json(stats_path(category, report_date), st)
    return {"ok": True, "category": category, "report_date": report_date,
            "summary_count": len(summary.get("rank_top", [])), "growth_count": len(glist)}

@router.get("/{category}", response_class=HTMLResponse)
def page(category: str, request: Request):
    # HTML strona kategorii
    # ładowanie growth i stats jeśli istnieją (z najnowszego dnia – prosto: bierzemy plik z load_latest)
    df, report_date = load_latest(category)
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
    return templates.TemplateResponse(f"trend/{category.lower()}/dashboard.html",
                                     {"request": request, "category": category, "growth": data_growth, "stats": data_stats, "report_date": report_date})

@router.get("/{category}/growth")
def api_growth(category: str):
    df, report_date = load_latest(category)
    if not report_date: return {"growth": []}
    try:
        with open(growth_path(category, report_date), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"growth": []}
