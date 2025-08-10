import pandas as pd, re
from ..core.utils import safe_int

STOP = {"podcast","odcinek","live","część","czesc","ft","feat","ep","premiera","rozmowa",
        "gość","gosc","prowadzący","z","u","vs","x"}

def _clean(t: str)->str:
    t = re.sub(r"\[[^\]]*\]|\([^\)]*\)|\{[^}]*\}", " ", t or "")
    t = re.sub(r"[#№]\s*\d+"," ", t)
    t = re.sub(r"\d{1,2}\s*/\s*\d{1,2}"," ", t)
    t = re.sub(r"[^\w\s\-\.'']", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+"," ", t).strip()

def _is_stop(w: str)->bool: return w.lower() in STOP
def _norm(n: str)->str: return " ".join(p.capitalize() for p in n.replace("'","'").split())

def extract_names_from_title(title: str):
    t = _clean(title)
    toks = t.split()
    out = set()
    for i in range(len(toks)-1):
        a,b = toks[i], toks[i+1]
        if a[:1].isupper() and b[:1].isupper() and not _is_stop(a) and not _is_stop(b):
            out.add(_norm(f"{a} {b}"))
    for m in re.findall(r"(?:ft\.?|feat\.?)\s+([A-Za-zÀ-ž][\w'.-]{2,})", t, flags=re.IGNORECASE):
        if not _is_stop(m): out.add(_norm(m))
    return sorted(out)

def rank_names(df: pd.DataFrame):
    rows = []
    for _, r in df.iterrows():
        names = extract_names_from_title(str(r.get("Title","")))
        v = safe_int(r.get("View_Count", 0))
        for n in names:
            rows.append({"name": n, "views": v})
    if not rows: return pd.DataFrame(columns=["name","views"])
    return (pd.DataFrame(rows)
            .groupby("name", as_index=False)["views"].sum()
            .sort_values("views", ascending=False))

def analyze(df):
    # Analiza podcast - zwraca ranking nazw
    rank = rank_names(df)
    return {"names_rank": rank.head(50).to_dict(orient="records")}
