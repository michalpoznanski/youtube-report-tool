import os, re, pandas as pd

def reports_dir():
    rd = os.environ.get("REPORTS_DIR")
    if rd: return rd
    base = os.environ.get("RAILWAY_VOLUME_PATH", "/mnt/volume")
    return os.path.join(base, "reports")

def find_latest(category: str):
    d = reports_dir()
    if not os.path.isdir(d): return None
    patt = re.compile(rf"report_{category.upper()}_\d{{4}}-\d{{2}}-\d{{2}}\.csv$")
    files = sorted([f for f in os.listdir(d) if patt.match(f)], reverse=True)
    if not files: return None
    return os.path.join(d, files[0])

def load_latest(category: str):
    p = find_latest(category)
    if not p: return None, None
    df = pd.read_csv(p)
    # raport_date z nazwy pliku
    report_date = os.path.basename(p).split("_")[-1].replace(".csv","")
    return df, report_date
