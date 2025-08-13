import os, json, logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timedelta
import csv
import glob
import logging
from typing import List, Dict
from ..core.loader import load_latest
from ..core.dispatcher import analyze_category
from ..core.growth import update_growth, _detect_is_short_from_csv_row
from ..core.store.trend_store import stats_path, growth_path, save_json, previous_date_str, load_growth_map_for_date
from ..core.stats import publish_hour_stats
from app.trend.utils.report_loader import build_rolling_leaderboard, _available_dates_for_category
from app.trend.utils.csv_audit import audit_csv

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
async def trend_dashboard_or_top(request: Request, category: str, mode: str = "rolling", date: str | None = None, days: int = 3, k: int = 15):
    """
    Główny endpoint trendów:
    - mode=daily → stary dashboard z przyrostami dziennymi
    - domyślnie (rolling) → przekierowanie do /trend/{category}/top
    """
    if mode == "daily":
        # istniejąca logika dzienna (zachowaj bieżący kod renderujący dashboard.html)
        try:
            category_upper = category.upper()
            reports_dir = "/mnt/volume/reports"
            if not date:
                # Znajdź najnowszy dostępny plik CSV
                pattern = os.path.join(reports_dir, f"report_{category_upper}_*.csv")
                files = sorted(glob.glob(pattern))
                if not files:
                    logging.warning(f"No CSV files found for pattern: {pattern}")
                    date = None
                else:
                    latest_file = os.path.basename(files[-1])
                    # Odczytaj datę z nazwy pliku: report_{CATEGORY}_{YYYY-MM-DD}.csv
                    try:
                        date = latest_file.split("_")[-1].replace(".csv", "")
                    except Exception:
                        date = None

            if not date:
                raise HTTPException(status_code=404, detail="No report date available for this category.")

            # Załaduj i oblicz przyrosty
            from app.trend.utils.report_loader import build_daily_growth
            records: List[Dict] = build_daily_growth(category, date)

            # Podział na Long‑form i Shorts
            long_records = [rec for rec in records if not rec.get("is_short")]
            short_records = [rec for rec in records if rec.get("is_short")]

            # Sortowanie i ograniczenie do TOP 50
            long_records = sorted(long_records, key=lambda x: x.get("views_today", 0), reverse=True)[:50]
            short_records = sorted(short_records, key=lambda x: x.get("views_today", 0), reverse=True)[:50]

            # Liczniki
            counts_total = len(records)
            counts_long = len(long_records)
            counts_shorts = len(short_records)

            logging.info(
                f"[TREND/DASHBOARD] category={category}, date={date}, total={counts_total}, "
                f"long={counts_long}, shorts={counts_shorts}"
            )

            return templates.TemplateResponse(
                f"trend/{category.lower()}/dashboard.html",
                {
                    "request": request,
                    "category": category,
                    "date": date,
                    "counts_total": counts_total,
                    "counts_long": counts_long,
                    "counts_shorts": counts_shorts,
                    "long_records": long_records,
                    "short_records": short_records,
                },
            )
        except Exception as e:
            logging.error(f"Error in trend_dashboard: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # rolling jako domyślny - przekierowanie do /top
    url = request.url_for("trend_top", category=category)
    qs = []
    if date: qs.append(f"date={date}")
    if days != 3: qs.append(f"days={days}")
    if k != 15: qs.append(f"k={k}")
    if qs:
        url = f"{url}?{'&'.join(qs)}"
    return RedirectResponse(url)

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
async def debug_csv(category: str, date: str = None):
    """Diagnostyczny endpoint sprawdzający pliki CSV z raportami."""
    try:
        category_upper = category.upper()
        reports_dir = "/mnt/volume/reports"
        # Znajdź wszystkie pliki z raportami dla danej kategorii
        pattern = f"report_{category_upper}_*.csv"
        glob_pattern = os.path.join(reports_dir, pattern)
        report_files = sorted(glob.glob(glob_pattern))

        if not report_files:
            logging.warning(f"No report files found for pattern: {glob_pattern}")
        
        # Ustal datę — jeśli nie podano, wybierz najnowszy raport
        if date:
            try:
                report_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        else:
            if report_files:
                # Ostatni plik w sortowanej liście to najnowszy
                latest_file = os.path.basename(report_files[-1])
                # Odczytaj datę z nazwy pliku
                try:
                    report_date_str = latest_file.split("_")[-1].replace(".csv", "")
                    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
                except Exception:
                    report_date = datetime.utcnow().date()
            else:
                report_date = datetime.utcnow().date()

        # Ścieżka do sprawdzanego pliku
        target_filename = f"report_{category_upper}_{report_date}.csv"
        target_path = os.path.join(reports_dir, target_filename)

        # Szczegóły pliku bieżącego dnia
        exists = os.path.isfile(target_path)
        size_bytes = os.path.getsize(target_path) if exists else 0
        rows = []
        sample = []
        if exists:
            with open(target_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = [row for row in reader]
                sample = rows[:5]
        
        # Szukaj pliku z poprzedniego dnia
        guessed_prev_date = (report_date - timedelta(days=1)).isoformat()
        prev_filename = f"report_{category_upper}_{guessed_prev_date}.csv"
        prev_path = os.path.join(reports_dir, prev_filename)
        prev_exists = os.path.isfile(prev_path)
        prev_rows_count = 0
        if prev_exists:
            with open(prev_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                prev_rows_count = sum(1 for _ in reader)

        return JSONResponse({
            "checked_path": target_path,
            "exists": exists,
            "size_bytes": size_bytes,
            "rows": len(rows),
            "sample": sample,
            "glob_candidates": [os.path.basename(f) for f in report_files],
            "guessed_prev_date": guessed_prev_date,
            "prev_exists": prev_exists,
            "prev_rows": prev_rows_count,
        })
    except Exception as e:
        logging.error(f"Error in /trend/{category}/_debug_csv: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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


@router.get("/trend/{category}/_audit_csv")
async def audit_csv_endpoint(category: str, days: int = 7):
    """
    Endpoint audytu CSV - wykrywa problemy z danymi i zwraca rekomendacje.
    
    Args:
        category (str): Kategoria do audytu
        days (int): Liczba dni do przeanalizowania (domyślnie 7)
    
    Returns:
        JSON z wynikami audytu i rekomendacjami
    """
    try:
        result = audit_csv(category, days=days)
        logging.info(f"[AUDIT] CSV audit completed for {category=}, days={days}")
        return result
    except Exception as e:
        logging.error(f"Error in CSV audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{category}/rolling", response_class=HTMLResponse)
async def trend_rolling(request: Request, category: str, date: str = None, days: int = 3, k: int = 15):
    category_upper = category.upper()
    if not date:
        # wybierz ostatnią dostępna datę
        dates = _available_dates_for_category(category_upper)
        if not dates:
            raise HTTPException(status_code=404, detail="Brak raportów CSV dla kategorii.")
        date = dates[-1]

    data = build_rolling_leaderboard(category_upper, date, days=max(1, days), top_k=max(1, k))
    logging.info(f"[ROLLING/DASHBOARD] {category=} {date=} days={days} k={k} longs={len(data['longs'])} shorts={len(data['shorts'])}")

    return templates.TemplateResponse(
        f"trend/{category}/rolling.html",
        {
            "request": request,
            "category": category,
            "date": data["end_date"],
            "days": data["days"],
            "top_k": data["top_k"],
            "long_records": data["longs"],
            "short_records": data["shorts"],
        },
    )


@router.get("/trend/{category}/top", response_class=HTMLResponse)
async def trend_top(request: Request, category: str, date: str | None = None, days: int = 3, k: int = 15):
    cat_up = category.upper()
    if not date:
        dates = _available_dates_for_category(cat_up)
        if not dates:
            raise HTTPException(status_code=404, detail="Brak raportów.")
        date = dates[-1]
    data = build_rolling_leaderboard(cat_up, date, days=max(1, days), top_k=max(1, k))
    return templates.TemplateResponse(
        f"trend/{category}/top.html",
        {"request": request, "category": category, "date": data["end_date"], "days": data["days"],
         "top_k": data["top_k"], "long_records": data["longs"], "short_records": data["shorts"]}
    )
