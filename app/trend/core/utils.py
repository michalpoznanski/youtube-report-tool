import math

def is_short(row):
    # Obsługa różnych wariantów kolumn
    vt = str(row.get("video_type", row.get("Video_Type", ""))).lower()
    if vt in {"short","shorts","shortvideo"}: return True
    dur = row.get("Duration", row.get("Video_Duration"))
    if dur is None: return False
    try:
        # Sekundy lub "mm:ss" / "hh:mm:ss"
        if isinstance(dur, str):
            parts = [int(x) for x in dur.split(":")]
            sec = 0
            for p in parts: sec = sec*60 + p
        else:
            sec = float(dur)
        return sec < 60
    except Exception:
        return False

def safe_int(x):
    try: return int(float(x))
    except: return 0
