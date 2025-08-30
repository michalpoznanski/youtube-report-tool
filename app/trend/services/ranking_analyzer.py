import pandas as pd
import json
from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RankingAnalyzer:
    def __init__(self, base_path_str: str = None):
        # Użyj naszych ustawień zamiast sztywnej ścieżki
        from app.config.settings import settings
        self.base_path = Path(base_path_str) if base_path_str else settings.reports_path
        self.base_path.mkdir(exist_ok=True)
        print(f"✅ RankingAnalyzer zainicjalizowany z ścieżką: {self.base_path}")

    def run_analysis_for_category(self, category: str) -> bool:
        """
        Główna metoda analizy rankingu dla danej kategorii.
        
        Args:
            category (str): Nazwa kategorii (np. "PODCAST", "FILM")
            
        Returns:
            bool: True jeśli analiza się powiodła, False w przeciwnym razie
        """
        try:
            today = date.today()
            print(f"🔄 Rozpoczynam analizę rankingu dla kategorii: {category}")
            
            # 1. Wczytaj dane
            today_csv_path = self.base_path / f"report_{category.upper()}_{today}.csv"
            yesterday_ranking_path = self.base_path / f"ranking_{category.upper()}_{today - timedelta(days=1)}.json"

            if not today_csv_path.exists():
                print(f"⚠️ Nie znaleziono dzisiejszego raportu CSV dla {category}. Pomijam analizę.")
                logger.warning(f"Nie znaleziono dzisiejszego raportu CSV dla {category}: {today_csv_path}")
                return False

            print(f"📊 Wczytuję dzisiejszy raport CSV: {today_csv_path}")
            df_today = pd.read_csv(today_csv_path)
            print(f"✅ Wczytano {len(df_today)} filmów z dzisiejszego raportu")

            # Wczytaj wczorajszy ranking (jeśli istnieje)
            yesterday_ranking = {'shorts': [], 'longform': []}
            if yesterday_ranking_path.exists():
                print(f"📊 Wczytuję wczorajszy ranking: {yesterday_ranking_path}")
                with open(yesterday_ranking_path, 'r', encoding='utf-8') as f:
                    yesterday_ranking = json.load(f)
                print(f"✅ Wczytano wczorajszy ranking: {len(yesterday_ranking['shorts'])} shorts, {len(yesterday_ranking['longform'])} longform")
            else:
                print(f"ℹ️ Brak wczorajszego rankingu - to pierwsza analiza dla {category}")

            # 2. Połącz i zaktualizuj
            print("🔄 Łączę dane z dzisiaj i wczoraj...")
            
            # Konwertuj wczorajszy ranking na DataFrame
            df_yesterday_shorts = pd.DataFrame(yesterday_ranking['shorts']) if yesterday_ranking['shorts'] else pd.DataFrame()
            df_yesterday_longform = pd.DataFrame(yesterday_ranking['longform']) if yesterday_ranking['longform'] else pd.DataFrame()
            
            if not df_yesterday_shorts.empty or not df_yesterday_longform.empty:
                df_yesterday = pd.concat([df_yesterday_shorts, df_yesterday_longform], ignore_index=True)
                print(f"📊 Wczorajszy ranking zawiera {len(df_yesterday)} filmów")
                
                # Połącz dane, zachowując nowsze (z dzisiaj)
                combined_df = pd.concat([df_today, df_yesterday], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset='Video_ID', keep='first')
                print(f"📊 Po połączeniu: {len(combined_df)} unikalnych filmów")
            else:
                combined_df = df_today
                print(f"📊 Używam tylko dzisiejszych danych: {len(combined_df)} filmów")

            # 3. Odfiltruj stare filmy (starsze niż 5 dni)
            print("🔄 Filtruję filmy starsze niż 5 dni...")
            five_days_ago = today - timedelta(days=5)
            
            # Konwertuj kolumnę daty na datetime
            combined_df['Date_of_Publishing'] = pd.to_datetime(combined_df['Date_of_Publishing'], errors='coerce')
            
            # Usuń wiersze z nieprawidłowymi datami
            combined_df = combined_df.dropna(subset=['Date_of_Publishing'])
            
            # Filtruj po dacie
            filtered_df = combined_df[combined_df['Date_of_Publishing'].dt.date >= five_days_ago]
            print(f"📊 Po filtrowaniu (5 dni): {len(filtered_df)} filmów")

            # 4. Podziel na formaty
            print("🔄 Dzielę filmy na formaty...")
            shorts_df = filtered_df[filtered_df['video_type'] == 'shorts']
            longform_df = filtered_df[filtered_df['video_type'] != 'shorts']  # Long-form
            
            print(f"📊 Shorts: {len(shorts_df)} filmów, Long-form: {len(longform_df)} filmów")

            # 5. Stwórz ranking (Top 10 po całkowitych wyświetleniach)
            print("🔄 Tworzę ranking Top 10...")
            
            # Sprawdź czy kolumna View_Count istnieje
            if 'View_Count' not in filtered_df.columns:
                print(f"❌ Brak kolumny View_Count w danych dla {category}")
                logger.error(f"Brak kolumny View_Count w danych dla {category}")
                return False
            
            # Sortuj i wybierz Top 10
            top_10_shorts = shorts_df.sort_values(by='View_Count', ascending=False).head(10).to_dict('records')
            top_10_longform = longform_df.sort_values(by='View_Count', ascending=False).head(10).to_dict('records')
            
            print(f"✅ Top 10 Shorts: {len(top_10_shorts)} filmów")
            print(f"✅ Top 10 Long-form: {len(top_10_longform)} filmów")

            # 6. Zapisz "pamięć" na jutro
            print("💾 Zapisuję ranking na jutro...")
            final_ranking = {
                'shorts': top_10_shorts, 
                'longform': top_10_longform,
                'analysis_date': today.isoformat(),
                'total_videos_analyzed': len(filtered_df),
                'shorts_count': len(shorts_df),
                'longform_count': len(longform_df)
            }
            
            output_path = self.base_path / f"ranking_{category.upper()}_{today}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_ranking, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Zapisano analizę rankingu dla {category.upper()} w pliku: {output_path}")
            logger.info(f"Pomyślnie wygenerowano ranking dla {category}: {len(top_10_shorts)} shorts, {len(top_10_longform)} longform")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas analizy rankingu dla {category}: {e}")
            logger.error(f"Błąd podczas analizy rankingu dla {category}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_latest_ranking(self, category: str) -> Dict[str, Any]:
        """
        Pobiera najnowszy ranking dla danej kategorii.
        
        Args:
            category (str): Nazwa kategorii
            
        Returns:
            Dict[str, Any]: Ranking lub pusty słownik jeśli nie istnieje
        """
        try:
            today = date.today()
            ranking_path = self.base_path / f"ranking_{category.upper()}_{today}.json"
            
            if ranking_path.exists():
                with open(ranking_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"ℹ️ Brak rankingu dla {category} z dzisiaj: {ranking_path}")
                return {"shorts": [], "longform": [], "error": "Brak rankingu"}
                
        except Exception as e:
            print(f"❌ Błąd podczas wczytywania rankingu dla {category}: {e}")
            logger.error(f"Błąd podczas wczytywania rankingu dla {category}: {e}")
            return {"shorts": [], "longform": [], "error": str(e)}
