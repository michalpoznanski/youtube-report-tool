try:
    import pandas as pd
    
    print("✅ Wszystkie importy w polityka analyzer udane")
except ImportError as e:
    print(f"❌ Błąd importu w polityka analyzer: {e}")
    import traceback
    traceback.print_exc()
    raise

# Placeholder: w przyszłości rozpoznawanie nazwisk + kontekst (np. "Tusk wybory", "Nawrocki snus")
def analyze(df):
    # zwróć pusty wynik na MVP
    return {"entities_rank": []}
