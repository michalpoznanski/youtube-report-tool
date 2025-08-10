def infer_is_short(title: str, duration: int | None = None) -> bool:
    if duration is not None:
        try:
            return int(duration) < 60
        except Exception:
            pass
    t = (title or "").lower()
    return "#shorts" in t or " shorts" in t or "[shorts]" in t

# Placeholder: w przyszłości rozpoznawanie nazwisk + kontekst (np. "Tusk wybrow", "Nawrocki snus")
def analyze(df, *, config=None) -> dict:
    # zwróć pusty wynik na MVP
    return {"entities_rank": []}
