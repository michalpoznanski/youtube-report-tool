from typing import Dict, Any
import pandas as pd
from .stats import publish_hour_stats
from ..analyzers import podcast as podcast_an
from ..analyzers import moto as moto_an
from ..analyzers import polityka as pol_an

def analyze_category(category: str, df: pd.DataFrame) -> Dict[str, Any]:
    cat = category.upper()
    if cat == "PODCAST":
        rank = podcast_an.rank_names(df)
        stats = publish_hour_stats(df)
        return {"type":"podcast", "rank_top": rank.head(50).to_dict(orient="records"), "stats": stats}
    if cat == "MOTO":
        res = moto_an.analyze(df)
        stats = publish_hour_stats(df)
        return {"type":"moto", **res, "stats": stats}
    if cat == "POLITYKA":
        res = pol_an.analyze(df)
        stats = publish_hour_stats(df)
        return {"type":"polityka", **res, "stats": stats}
    return {"type":"unknown", "rank_top": [], "stats": {}}
