try:
    import csv
    from typing import Dict, Any, List
    from datetime import date
    from pathlib import Path
    from app.trend.core.store.trend_store import report_path_for_date
    
    print("✅ Wszystkie importy w trend csv_loader udane")
except ImportError as e:
    print(f"❌ Błąd importu w trend csv_loader: {e}")
    import traceback
    traceback.print_exc()
    raise

def normalize_key(k: str) -> str:
    """Normalizuj klucz: strip, lower, usuń BOM, zamień spacje/- na _"""
    if not k:
        return ""
    
    # Usuń BOM
    k = k.replace('\ufeff', '')
    
    # Strip i lower
    k = k.strip().lower()
    
    # Zamień spacje i myślniki na podkreślniki
    k = k.replace(' ', '_').replace('-', '_')
    
    return k

def map_headers(row: Dict[str, Any]) -> Dict[str, Any]:
    """Przemapuj klucze na kanoniczne"""
    normalized = {}
    
    # Normalizuj wszystkie klucze
    for key, value in row.items():
        norm_key = normalize_key(key)
        normalized[norm_key] = value
    
    # Mapowanie na kanoniczne pola
    result = {
        "video_id": None,
        "title": None,
        "channel": None,
        "views": 0,
        "duration_seconds": None,
        "published_at": None,
        "tags": None,
        "description": None
    }
    
    # video_id: z (video_id, videoid, id)
    for key in ["video_id", "videoid", "id"]:
        if key in normalized and normalized[key]:
            result["video_id"] = str(normalized[key]).strip()
            break
    
    # title: (title, video_title)
    for key in ["title", "video_title"]:
        if key in normalized and normalized[key]:
            result["title"] = str(normalized[key]).strip()
            break
    
    # channel: (channel, channel_title, channeltitle)
    for key in ["channel", "channel_title", "channeltitle"]:
        if key in normalized and normalized[key]:
            result["channel"] = str(normalized[key]).strip()
            break
    
    # views: preferuj dzienne views_today, fallback total
    views_today = None
    total_views = None
    
    for key in ["views_today", "views", "view_count", "viewcount"]:
        if key in normalized and normalized[key]:
            try:
                val = int(float(normalized[key]))
                if key == "views_today":
                    views_today = val
                else:
                    total_views = val
            except (ValueError, TypeError):
                pass
    
    # Preferuj dzienne, fallback total
    if views_today is not None:
        result["views"] = views_today
    elif total_views is not None:
        result["views"] = total_views
    
    # duration_seconds: z (duration, duration_seconds, length_sec)
    for key in ["duration_seconds", "duration", "length_sec"]:
        if key in normalized and normalized[key]:
            try:
                result["duration_seconds"] = int(float(normalized[key]))
                break
            except (ValueError, TypeError):
                pass
    
    # published_at: (published_at, upload_date, publishedat)
    for key in ["published_at", "upload_date", "publishedat"]:
        if key in normalized and normalized[key]:
            result["published_at"] = str(normalized[key]).strip()
            break
    
    # tags / description
    for key in ["tags", "description"]:
        if key in normalized and normalized[key]:
            result[key] = str(normalized[key]).strip()
    
    return result

def read_csv_for_date(category: str, d: date) -> List[Dict[str, Any]]:
    """Wczytaj CSV dla daty i znormalizuj"""
    csv_path = report_path_for_date(category, d)
    if not csv_path or not csv_path.exists():
        return []
    
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Znormalizuj nagłówki
                normalized = map_headers(row)
                
                # Pomiń wiersze bez video_id
                if normalized["video_id"]:
                    rows.append(normalized)
    
    except Exception as e:
        print(f"Error loading CSV {csv_path}: {e}")
    
    return rows
