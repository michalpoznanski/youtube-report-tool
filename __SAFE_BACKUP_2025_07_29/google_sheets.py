import gspread
import pandas as pd
import os
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_data_from_url(url, credentials_file=None):
    """
    Uniwersalna funkcja do pobierania danych z Google Sheets.
    Używana przez oba boty: YT2 i analiza nazwisk.
    """
    # Upewnij się, że ścieżka do service_account.json jest absolutna
    if credentials_file is None:
        # Pobierz katalog gdzie jest uruchamiany bot
        bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_file = os.path.join(bot_dir, "data", "config", "service_account.json")
    
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)

        # Pobierz arkusz na podstawie URL
        sheet = client.open_by_url(url)
        worksheet = sheet.get_worksheet(0)  # Pierwsza zakładka

        # Wczytaj dane jako lista słowników i konwertuj na DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych z Google Sheets: {e}")
        return None 