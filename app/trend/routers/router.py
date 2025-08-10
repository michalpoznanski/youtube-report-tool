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
logger.info("[TREND/ROUTER] Router module loaded successfully")
router = APIRouter(prefix="/trend", tags=["trend"])

@router.get("/test")
def test_endpoint():
    """Test endpoint żeby sprawdzić czy routing w ogóle działa"""
    logger.info("[TREND/TEST] Test endpoint hit!")
    return {"message": "Trend router działa!", "status": "ok"}

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
    
    logger.info(f'[TREND/PAGE] Loading page for category: {category}')
    logger.info(f'[TREND/PAGE] Request URL: {request.url}')
    logger.info(f'[TREND/PAGE] Request method: {request.method}')
    
    # 1. Ustal report_date - spróbuj z load_latest, fallback z najnowszego CSV
    df, report_date = load_latest(category)
    if not report_date:
        # Fallback: znajdź najnowszy CSV
        from app.trend.core.store.trend_store import list_report_files
        from datetime import datetime
        
        csv_files = list_report_files(category)
        if csv_files:
            report_date = csv_files[-1][0].strftime("%Y-%m-%d")
        else:
            return templates.TemplateResponse(
                f"trend/{category.lower()}/dashboard.html",
                {"request": request, "category": category, "error": "Brak danych CSV"}
            )
    
    # 2. Spróbuj wczytać growth JSON
    data_growth = None
    data_stats = None
    
    try:
        # Sprawdź czy istnieje growth JSON
        growth_file = growth_path(category, report_date)
        if Path(growth_file).exists():
            with open(growth_file, "r", encoding="utf-8") as f:
                data_growth = json.load(f)
                
                # Sprawdź czy ma views_yesterday/delta
                has_complete_data = all(
                    item.get("views_yesterday") is not None and item.get("delta") is not None
                    for item in data_growth.get("growth", [])
                )
                
                if not has_complete_data:
                    data_growth = None  # Wymuś przebudowanie z CSV
    except Exception:
        data_growth = None
    
    # 3. Jeśli brak growth JSON lub niekompletne dane - zbuduj z CSV lub użyj fallback
    if not data_growth:
        from app.trend.core.growth import build_growth_from_csv, save_growth_and_stats
        from app.trend.core.store.trend_store import list_report_files, list_growth_files
        from datetime import datetime, date
        
        try:
            # Ustal datę: najnowszą z list_report_files
            csv_files = list_report_files(category)
            if csv_files:
                # csv_files to lista (datetime, Path) - weź najnowszą datę
                latest_date, latest_path = csv_files[-1]
                report_dt = latest_date.date()
                
                logger.info(f'[TREND/CSV] Building growth from CSV for {category} at {report_dt.isoformat()}')
                
                # Zbuduj growth z CSV
                data_growth = build_growth_from_csv(category, report_dt)
                
                # Zapisz growth i stats
                save_growth_and_stats(category, report_dt, data_growth)
                
                # Aktualizuj report_date
                report_date = report_dt.strftime("%Y-%m-%d")
                
            else:
                # Fallback: użyj istniejącego growth JSON
                logger.warning(f'[TREND/CSV] No CSV files found for {category}, trying growth JSON fallback')
                growth_files = list_growth_files(category)
                logger.info(f'[TREND/FALLBACK] Found {len(growth_files)} growth files for {category}')
                
                if growth_files:
                    # Weź najnowszy growth JSON
                    latest_date, latest_path = growth_files[-1]
                    report_date = latest_date.strftime("%Y-%m-%d")
                    logger.info(f'[TREND/FALLBACK] Using growth file: {latest_path} from {report_date}')
                    
                    try:
                        with open(latest_path, "r", encoding="utf-8") as f:
                            data_growth = json.load(f)
                        logger.info(f'[TREND/FALLBACK] Loaded growth from {latest_path}, items: {len(data_growth.get("growth", []))}')
                    except Exception as e:
                        logger.error(f'[TREND/FALLBACK] Error loading growth: {e}')
                        data_growth = {"growth": []}
                else:
                    logger.warning(f'[TREND/CSV] No growth files found for {category}')
                    data_growth = {"growth": []}
                
        except Exception as e:
            logger.exception(f'[TREND/CSV] Error building growth from CSV: {e}')
            data_growth = {"growth": []}
    
    # 4. Policz statystyki
    growth_items = data_growth.get("growth", [])
    total = len(growth_items)
    
    long_items = [x for x in growth_items if not x.get("is_short", False)]
    short_items = [x for x in growth_items if x.get("is_short", False)]
    
    # Sortowanie po views_today malejąco
    long_items = sorted(long_items, key=lambda r: int(r.get("views_today") or 0), reverse=True)[:50]
    short_items = sorted(short_items, key=lambda r: int(r.get("views_today") or 0), reverse=True)[:50]
    
    logger.info(f'[TREND] {category}: report_date={report_date}, total={total}, long={len(long_items)}, short={len(short_items)}')
    logger.info(f'[TREND] Final data_growth keys: {list(data_growth.keys()) if data_growth else "None"}')
    
    return templates.TemplateResponse(
        f"trend/{category.lower()}/dashboard.html",
        {
            "request": request,
            "category": category,
            "report_date": report_date,
            "total": total,
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

@router.get("/{category}/_debug_prev")
def debug_prev(category: str):
    """Debug endpoint pokazujący CSV i growth dla dzisiejszej i wczorajszej daty"""
    from app.trend.core.store.trend_store import list_report_files, get_prev_date
    from app.trend.core.loader import load_csv
    from datetime import datetime
    
    out = {
        "category": category,
        "today_report_date": None,
        "today_csv": None,
        "prev_date": None,
        "prev_csv": None,
        "today_rows": 0,
        "prev_rows": 0,
        "sample_today": [],
        "sample_prev": []
    }
    
    try:
        # Znajdź najnowszy CSV
        csv_files = list_report_files(category)
        if csv_files:
            today_dt = csv_files[-1][0]
            today_csv_path = csv_files[-1][1]
            out["today_report_date"] = today_dt.strftime("%Y-%m-%d")
            out["today_csv"] = str(today_csv_path)
            
            # Wczytaj dzisiejszy CSV
            today_rows = load_csv(category, today_dt)
            out["today_rows"] = len(today_rows)
            out["sample_today"] = today_rows[:3] if today_rows else []
            
            # Znajdź wczorajszy CSV
            prev_dt = get_prev_date(category, today_dt)
            if prev_dt:
                out["prev_date"] = prev_dt.strftime("%Y-%m-%d")
                
                # Znajdź ścieżkę do wczorajszego CSV
                for dt, path in csv_files:
                    if dt == prev_dt:
                        out["prev_csv"] = str(path)
                        break
                
                # Wczytaj wczorajszy CSV
                prev_rows = load_csv(category, prev_dt)
                out["prev_rows"] = len(prev_rows)
                out["sample_prev"] = prev_rows[:3] if prev_rows else []
    
    except Exception as e:
        out["error"] = str(e)
    
    return out

@router.get("/{category}/_debug_csv")
def debug_csv(category: str, date: str = None):
    """Debug endpoint pokazujący CSV dla daty"""
    from app.trend.core.store.trend_store import list_report_files
    from app.trend.core.csv_loader import read_csv_for_date
    from datetime import datetime, date
    
    out = {
        "category": category,
        "date": None,
        "today_rows": 0,
        "prev_rows": 0,
        "sample_today": None,
        "sample_prev": None,
        "today_path": None,
        "prev_path": None
    }
    
    try:
        if date:
            # Użyj wskazanej daty
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            # Użyj najnowszego CSV
            csv_files = list_report_files(category)
            if not csv_files:
                return out
            # csv_files to lista (datetime, Path) - weź najnowszą datę
            latest_date, latest_path = csv_files[-1]
            target_date = latest_date.date()
        
        out["date"] = target_date.isoformat()
        
        # Wczytaj dzisiejszy CSV
        today = read_csv_for_date(category, target_date)
        out["today_rows"] = len(today)
        out["sample_today"] = today[0] if today else None
        
        # Znajdź ścieżkę do dzisiejszego CSV
        from app.trend.core.store.trend_store import report_path_for_date
        today_path = report_path_for_date(category, target_date)
        out["today_path"] = str(today_path) if today_path else None
        
        # Wczytaj wczorajszy CSV
        from app.trend.core.store.trend_store import prev_date
        prev_d = prev_date(target_date)
        prev = read_csv_for_date(category, prev_d)
        out["prev_rows"] = len(prev)
        out["sample_prev"] = prev[0] if prev else None
        
        # Znajdź ścieżkę do wczorajszego CSV
        prev_path = report_path_for_date(category, prev_d)
        out["prev_path"] = str(prev_path) if prev_path else None
        
    except Exception as e:
        out["error"] = str(e)
    
    return out

@router.get("/{category}/rebuild-from-csv")
def rebuild_from_csv(category: str, date: str = None):
    """Przebuduj growth z CSV dla wskazanej daty"""
    from app.trend.core.growth import build_growth_from_csv, save_growth_and_stats
    from app.trend.core.store.trend_store import list_report_files
    from datetime import datetime, date
    
    try:
        if date:
            # Użyj wskazanej daty
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            # Użyj najnowszego CSV
            csv_files = list_report_files(category)
            if not csv_files:
                return {"ok": False, "error": "Brak plików CSV"}
            # csv_files to lista (datetime, Path) - weź najnowszą datę
            latest_date, latest_path = csv_files[-1]
            target_date = latest_date.date()
        
        # Zbuduj growth z CSV
        data_growth = build_growth_from_csv(category, target_date)
        
        # Zapisz growth i stats
        save_growth_and_stats(category, target_date, data_growth)
        
        return {
            "ok": True,
            "category": category,
            "date": target_date.isoformat(),
            "items": len(data_growth.get("growth", []))
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}
