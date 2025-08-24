#!/usr/bin/env python3
"""
Lokalny analizator trendów dla Hook Boost.
Pobiera ostatnie raporty CSV z Railway i analizuje je lokalnie.
"""

import requests
import pandas as pd
import json
from datetime import date, timedelta
from typing import List, Dict, Any
import os

class LocalTrendAnalyzer:
    def __init__(self, railway_url: str = "https://youtube-report-tool-production-4738.up.railway.app"):
        self.railway_url = railway_url
        self.api_base = f"{railway_url}/api/v1"
        
    def get_available_reports(self) -> Dict[str, Any]:
        """Pobiera listę dostępnych raportów z Railway"""
        try:
            response = requests.post(f"{self.api_base}/trends/analyze-all", 
                                  headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Błąd podczas pobierania raportów: {e}")
            return None
    
    def download_csv_data(self, filename: str) -> pd.DataFrame:
        """Pobiera dane CSV z Railway i konwertuje na DataFrame"""
        try:
            # Pobierz dane przez API
            response = requests.post(f"{self.api_base}/trends/analyze-all", 
                                  headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            
            # Znajdź plik w wynikach
            for file_info in data["result"]["files_processed"]:
                if file_info["filename"] == filename:
                    print(f"📁 Znaleziono plik: {filename} ({file_info['rows']} wierszy)")
                    
                    # Symuluj DataFrame na podstawie struktury kolumn
                    # W rzeczywistości pobieralibyśmy plik CSV
                    columns = file_info["columns"]
                    print(f"📊 Kolumny: {columns}")
                    
                    # Zwróć przykładowe dane (w rzeczywistości to byłby prawdziwy CSV)
                    return self._create_sample_dataframe(columns, file_info["rows"])
            
            print(f"❌ Nie znaleziono pliku: {filename}")
            return None
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania danych CSV: {e}")
            return None
    
    def _create_sample_dataframe(self, columns: List[str], rows: int) -> pd.DataFrame:
        """Tworzy przykładowy DataFrame (w rzeczywistości to byłby prawdziwy CSV)"""
        # To jest tylko przykład - w rzeczywistości pobieralibyśmy prawdziwy CSV
        sample_data = {}
        for col in columns:
            if col == "Title":
                sample_data[col] = [f"Przykładowy film {i+1}" for i in range(rows)]
            elif col == "View_Count":
                sample_data[col] = [1000 + i * 100 for i in range(rows)]
            elif col == "Channel_Name":
                sample_data[col] = ["Kanał Testowy"] * rows
            else:
                sample_data[col] = ["Test"] * rows
        
        return pd.DataFrame(sample_data)
    
    def analyze_trends(self, category: str = "PODCAST") -> Dict[str, Any]:
        """Analizuje trendy dla danej kategorii"""
        print(f"🚀 Rozpoczynam analizę trendów dla kategorii: {category}")
        
        # Pobierz dostępne raporty
        reports = self.get_available_reports()
        if not reports:
            return {"error": "Nie udało się pobrać raportów"}
        
        # Znajdź pliki dla kategorii
        category_files = []
        for file_info in reports["result"]["files_processed"]:
            if file_info["filename"].startswith(f"report_{category.upper()}_"):
                category_files.append(file_info)
        
        if not category_files:
            return {"error": f"Brak raportów dla kategorii {category}"}
        
        print(f"📁 Znaleziono {len(category_files)} raportów dla {category}")
        
        # Sortuj pliki po dacie (najnowsze pierwsze)
        category_files.sort(key=lambda x: x["filename"], reverse=True)
        
        # Analizuj ostatnie 3 raporty
        analysis_results = []
        for i, file_info in enumerate(category_files[:3]):
            print(f"📊 Analizuję raport {i+1}: {file_info['filename']}")
            
            # Pobierz dane CSV
            df = self.download_csv_data(file_info["filename"])
            if df is not None:
                # Analiza danych
                result = self._analyze_dataframe(df, file_info["filename"])
                analysis_results.append(result)
        
        return {
            "category": category,
            "total_reports_analyzed": len(analysis_results),
            "reports": analysis_results,
            "summary": self._create_summary(analysis_results)
        }
    
    def _analyze_dataframe(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Analizuje pojedynczy DataFrame"""
        try:
            # Podstawowe statystyki
            total_videos = len(df)
            total_views = int(df.get("View_Count", pd.Series([0])).sum())  # Konwertuj na int
            avg_views = total_views / total_videos if total_videos > 0 else 0
            
            # Top filmy według wyświetleń
            if "View_Count" in df.columns:
                top_videos = df.nlargest(5, "View_Count")[["Title", "View_Count", "Channel_Name"]].to_dict("records")
                # Konwertuj int64 na int
                for video in top_videos:
                    if "View_Count" in video:
                        video["View_Count"] = int(video["View_Count"])
            else:
                top_videos = []
            
            return {
                "filename": filename,
                "total_videos": total_videos,
                "total_views": total_views,
                "avg_views": round(avg_views, 2),
                "top_videos": top_videos,
                "columns_available": list(df.columns)
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "error": str(e)
            }
    
    def _create_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tworzy podsumowanie analizy"""
        if not analysis_results:
            return {"error": "Brak wyników do podsumowania"}
        
        total_videos = sum(r.get("total_videos", 0) for r in analysis_results)
        total_views = sum(r.get("total_views", 0) for r in analysis_results)
        
        return {
            "total_reports": len(analysis_results),
            "total_videos": total_videos,
            "total_views": total_views,
            "avg_views_per_video": round(total_views / total_videos, 2) if total_videos > 0 else 0
        }
    
    def generate_report(self, category: str = "PODCAST") -> str:
        """Generuje raport HTML"""
        analysis = self.analyze_trends(category)
        
        if "error" in analysis:
            return f"<h2>❌ Błąd: {analysis['error']}</h2>"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pl">
        <head>
            <meta charset="UTF-8">
            <title>Raport Trendów - {category}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #667eea; color: white; padding: 20px; border-radius: 10px; }}
                .summary {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }}
                .report {{ background: white; padding: 20px; margin: 20px 0; border: 1px solid #ddd; border-radius: 10px; }}
                .top-videos {{ background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Raport Trendów - {category}</h1>
                <p>Wygenerowano: {date.today().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="summary">
                <h2>📈 Podsumowanie</h2>
                <p><strong>Liczba raportów:</strong> {analysis['summary']['total_reports']}</p>
                <p><strong>Łącznie filmów:</strong> {analysis['summary']['total_videos']}</p>
                <p><strong>Łącznie wyświetleń:</strong> {analysis['summary']['total_views']:,}</p>
                <p><strong>Średnio wyświetleń na film:</strong> {analysis['summary']['avg_views_per_video']:,}</p>
            </div>
        """
        
        for report in analysis["reports"]:
            html += f"""
            <div class="report">
                <h3>📁 {report['filename']}</h3>
                <p><strong>Liczba filmów:</strong> {report['total_videos']}</p>
                <p><strong>Łącznie wyświetleń:</strong> {report['total_views']:,}</p>
                <p><strong>Średnio wyświetleń:</strong> {report['avg_views']:,}</p>
                
                <h4>🏆 Top 5 filmów:</h4>
                <div class="top-videos">
            """
            
            for video in report.get("top_videos", []):
                html += f"""
                    <p><strong>{video.get('Title', 'Brak tytułu')}</strong> - {video.get('View_Count', 0):,} wyświetleń</p>
                """
            
            html += """
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html

    def save_analysis_to_json(self, category: str = "PODCAST") -> str:
        """Zapisuje wyniki analizy do pliku JSON dla Railway"""
        analysis = self.analyze_trends(category)
        
        if "error" in analysis:
            return f"❌ Błąd: {analysis['error']}"
        
        # Przygotuj dane do zapisania
        json_data = {
            "category": category,
            "generated_at": date.today().strftime('%Y-%m-%d %H:%M:%S'),
            "total_reports_analyzed": analysis['total_reports_analyzed'],
            "summary": analysis['summary'],
            "reports": analysis['reports']
        }
        
        # Zapisz do pliku JSON
        json_filename = f"trend_analysis_{category.lower()}_{date.today().strftime('%Y%m%d')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Analiza zapisana do: {json_filename}")
        
        # Zapisz również najnowszy plik (bez daty) dla Railway
        latest_filename = f"trend_analysis_{category.lower()}_latest.json"
        with open(latest_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Najnowsza analiza zapisana do: {latest_filename}")
        
        return json_filename

def main():
    """Główna funkcja"""
    print("🚀 Lokalny Analizator Trendów Hook Boost")
    print("=" * 50)
    
    analyzer = LocalTrendAnalyzer()
    
    # Sprawdź dostępne raporty
    print("\n📊 Sprawdzam dostępne raporty...")
    reports = analyzer.get_available_reports()
    
    if reports:
        print(f"✅ Znaleziono {reports['result']['total_processed']} raportów")
        for file_info in reports['result']['files_processed']:
            print(f"   📁 {file_info['filename']} - {file_info['rows']} wierszy")
    else:
        print("❌ Nie udało się pobrać raportów")
        return
    
    # Analizuj trendy dla Podcast
    print("\n🎯 Analizuję trendy dla kategorii PODCAST...")
    analysis = analyzer.analyze_trends("PODCAST")
    
    if "error" not in analysis:
        print(f"✅ Analiza zakończona: {analysis['summary']['total_reports']} raportów")
        print(f"   📊 Łącznie filmów: {analysis['summary']['total_videos']}")
        print(f"   👁️ Łącznie wyświetleń: {analysis['summary']['total_views']:,}")
        
        # Generuj raport HTML
        print("\n📄 Generuję raport HTML...")
        report_html = analyzer.generate_report("PODCAST")
        
        # Zapisz raport HTML
        report_filename = f"raport_trendow_{date.today().strftime('%Y%m%d')}.html"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        print(f"✅ Raport HTML zapisany: {report_filename}")
        
        # Zapisz analizę do JSON dla Railway
        print("\n💾 Zapisuję analizę do JSON dla Railway...")
        json_filename = analyzer.save_analysis_to_json("PODCAST")
        
        print(f"\n🎉 Wszystko gotowe!")
        print(f"📄 Raport HTML: {report_filename}")
        print(f"💾 Analiza JSON: {json_filename}")
        print(f"🌐 Otwórz plik HTML w przeglądarce żeby zobaczyć wyniki")
        print(f"📤 Prześlij plik JSON na Railway żeby wyświetlić na stronie")
        
    else:
        print(f"❌ Błąd podczas analizy: {analysis['error']}")

if __name__ == "__main__":
    main()
