# app/trend/utils/csv_audit.py

import csv
import os
import glob
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Rekomendacje zmian w generatorze raportów
AUDIT_RECOMMENDATION = """
REKOMENDACJE POPRAWY GENERATORA RAPORTÓW CSV:

1. KLASYFIKACJA SHORT vs LONG:
   - Ustawić video_type = "shorts" jeśli duration_seconds < 180
   - Ustawić video_type = "long" jeśli duration_seconds >= 180
   - Ignorować tagi #short/#shorts w logice generatora

2. KOLUMNY DO USUNIĘCIA:
   - Names_Extracted - niepotrzebna, powoduje zamieszanie

3. POLA DOCELOWE (zachować tylko te):
   - Video_ID (wymagane, unikalne)
   - Title (wymagane)
   - Channel_Name (wymagane, niepuste)
   - View_Count (wymagane, int)
   - Duration (wymagane, ISO 8601 format: PT1H33M7S)
   - Tags (opcjonalne)
   - Description (opcjonalne)
   - Video_Published_At (opcjonalne)
   - Channel_ID (opcjonalne)
   - video_type (wymagane: "shorts" lub "long")

4. WALIDACJA PRZED ZAPISEM:
   - Duration: parsuje się do sekund (regex PT...)
   - View_Count: liczba całkowita >= 0
   - Channel_Name: niepuste, min 1 znak
   - Video_ID: unikalne w ramach dnia
   - video_type: tylko "shorts" lub "long"

5. FORMAT DURATION:
   - Zawsze ISO 8601: PT1H33M7S, PT45S, PT1M5S
   - Konwersja do sekund przed zapisem
   - Walidacja regex: PT(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?

6. LOGIKA KLASYFIKACJI:
   if duration_seconds < 180:
       video_type = "shorts"
   else:
       video_type = "long"
"""

def audit_csv(category: str, days: int = 7, reports_dir: str = "/mnt/volume/reports") -> dict:
    """
    Skanuje ostatnie N dni plików CSV i wykrywa problemy z danymi.
    
    Args:
        category (str): Kategoria do audytu (np. "podcast")
        days (int): Liczba dni do przeanalizowania
        reports_dir (str): Katalog z plikami CSV
    
    Returns:
        dict: Wyniki audytu z licznikami, przykładowymi wierszami i listą plików
    """
    category_upper = category.upper()
    pattern = os.path.join(reports_dir, f"report_{category_upper}_*.csv")
    files = sorted(glob.glob(pattern))
    
    if not files:
        return {
            "error": f"Brak plików CSV dla kategorii {category_upper}",
            "files": [],
            "counts": {},
            "sample_rows": [],
            "recommendations": AUDIT_RECOMMENDATION
        }
    
    # Ogranicz do ostatnich N dni
    recent_files = files[-days:] if len(files) > days else files
    
    # Liczniki problemów
    counts = {
        "total_files": len(recent_files),
        "total_rows": 0,
        "names_extracted_present": 0,
        "names_extracted_count": 0,
        "video_type_vs_duration_mismatch": 0,
        "empty_channel_name": 0,
        "invalid_duration_format": 0,
        "non_integer_view_count": 0,
        "missing_video_type": 0,
        "invalid_video_type_values": 0
    }
    
    sample_rows = []
    all_columns = set()
    
    # Regex do walidacji Duration ISO 8601
    duration_pattern = re.compile(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$')
    
    for filepath in recent_files:
        try:
            with open(filepath, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                all_columns.update(reader.fieldnames or [])
                
                for row in reader:
                    counts["total_rows"] += 1
                    
                    # Sprawdź obecność Names_Extracted
                    if "Names_Extracted" in row:
                        counts["names_extracted_present"] += 1
                        if row["Names_Extracted"]:
                            counts["names_extracted_count"] += 1
                    
                    # Sprawdź niespójność video_type vs duration
                    video_type = row.get("video_type", "").lower().strip()
                    duration_str = row.get("Duration", "")
                    
                    if video_type and duration_str:
                        # Próbuj sparsować duration
                        duration_match = duration_pattern.match(duration_str)
                        if duration_match:
                            hours = int(duration_match.group(1) or 0)
                            minutes = int(duration_match.group(2) or 0)
                            seconds = int(duration_match.group(3) or 0)
                            duration_seconds = hours * 3600 + minutes * 60 + seconds
                            
                            # Sprawdź niespójność
                            if (video_type == "long" and duration_seconds < 180) or \
                               (video_type == "shorts" and duration_seconds >= 180):
                                counts["video_type_vs_duration_mismatch"] += 1
                                if len(sample_rows) < 10:
                                    sample_rows.append({
                                        "file": os.path.basename(filepath),
                                        "video_type": video_type,
                                        "duration": duration_str,
                                        "duration_seconds": duration_seconds,
                                        "title": row.get("Title", "")[:50]
                                    })
                        else:
                            counts["invalid_duration_format"] += 1
                    
                    # Sprawdź brak lub puste Channel_Name
                    channel_name = row.get("Channel_Name", "").strip()
                    if not channel_name:
                        counts["empty_channel_name"] += 1
                    
                    # Sprawdź View_Count
                    view_count = row.get("View_Count", "")
                    if view_count and not str(view_count).isdigit():
                        counts["non_integer_view_count"] += 1
                    
                    # Sprawdź video_type
                    if not video_type:
                        counts["missing_video_type"] += 1
                    elif video_type not in ["shorts", "long"]:
                        counts["invalid_video_type_values"] += 1
                        
        except Exception as e:
            logging.error(f"Błąd podczas audytu pliku {filepath}: {e}")
            continue
    
    # Dodaj przykładowe wiersze z problemami
    if not sample_rows and counts["total_rows"] > 0:
        # Dodaj przykładowy wiersz z pierwszego pliku
        try:
            with open(recent_files[0], newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    sample_rows.append({
                        "file": os.path.basename(recent_files[0]),
                        "sample_data": {k: str(v)[:100] for k, v in row.items()}
                    })
                    break
        except Exception:
            pass
    
    return {
        "category": category,
        "audit_period_days": days,
        "files": [os.path.basename(f) for f in recent_files],
        "all_columns_found": list(all_columns),
        "counts": counts,
        "sample_rows": sample_rows[:10],  # Maksymalnie 10 przykładowych wierszy
        "recommendations": AUDIT_RECOMMENDATION,
        "audit_timestamp": datetime.now().isoformat()
    }
