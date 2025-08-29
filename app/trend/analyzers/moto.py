try:
    import pandas as pd
    
    print("✅ Wszystkie importy w moto analyzer udane")
except ImportError as e:
    print(f"❌ Błąd importu w moto analyzer: {e}")
    import traceback
    traceback.print_exc()
    raise

# Placeholder: w przyszłości rozpoznawanie marek/modeli (np. "BMW", "Audi", "Golf GTI")
def analyze(df):
    # zwróć pusty wynik na MVP
    return {"brands_rank": []}
