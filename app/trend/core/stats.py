try:
    import pandas as pd
    from .utils import is_short, safe_int
    
    print("✅ Wszystkie importy w trend stats udane")
except ImportError as e:
    print(f"❌ Błąd importu w trend stats: {e}")
    import traceback
    traceback.print_exc()
    raise

def publish_hour_stats(df: pd.DataFrame):
    # oczekujemy kolumny Published_At lub Date_of_Publishing (ISO)
    col = "Published_At" if "Published_At" in df.columns else ("Date_of_Publishing" if "Date_of_Publishing" in df.columns else None)
    if not col: return {"longs": {}, "shorts": {}}
    tmp = df.copy()
    # parse hour
    hours = []
    for _, r in tmp.iterrows():
        v = str(r.get(col, ""))[:19]  # "YYYY-MM-DDTHH:MM:SS"
        try:
            h = int(v[11:13]) if len(v) >= 13 else None
        except:
            h = None
        hours.append(h)
    tmp["__hour"] = hours
    tmp["__is_short"] = tmp.apply(is_short, axis=1)
    # agregacje: liczba publikacji i suma wyświetleń per godzina
    def agg(df2):
        g = df2.groupby("__hour").agg(
            count=("Video_ID","count"),
            views=("View_Count", lambda x: int(pd.to_numeric(x, errors="coerce").fillna(0).sum()))
        ).reset_index()
        # top hour by views
        if g.empty: return {"top_hour": None, "by_hour": {}}
        best = g.sort_values("views", ascending=False).iloc[0]
        mapping = {int(row["__hour"]): {"count": int(row["count"]), "views": int(row["views"])} for _, row in g.iterrows() if pd.notna(row["__hour"])}
        return {"top_hour": int(best["__hour"]), "by_hour": mapping}
    longs = agg(tmp[~tmp["__is_short"]])
    shorts = agg(tmp[tmp["__is_short"]])
    return {"longs": longs, "shorts": shorts}
