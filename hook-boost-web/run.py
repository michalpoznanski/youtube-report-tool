import os
import sys
from pathlib import Path

# Dodaj główny katalog projektu do ścieżki Pythona, aby znaleźć moduł 'app'
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    # Teraz ścieżka 'app.main:app' będzie działać poprawnie
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
