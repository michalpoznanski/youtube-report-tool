import pandas as pd
from tabulate import tabulate
from datetime import datetime
import json

def generate_text_report(keywords_data, title="Analiza słów kluczowych"):
    """Generuje tekstowy raport z analizy słów kluczowych."""
    report = []
    report.append(f"=== {title} ===")
    report.append(f"Data generowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    for category, keywords in keywords_data.items():
        report.append(f"--- {category.upper()} ---")
        if keywords:
            for i, (word, count) in enumerate(keywords.items(), 1):
                report.append(f"{i:2d}. {word:20s} - {count:3d} wystąpień")
        else:
            report.append("Brak danych")
        report.append("")
    
    return "\n".join(report)

def generate_table_report(keywords_data, title="Analiza słów kluczowych"):
    """Generuje raport w formie tabeli."""
    all_data = []
    
    for category, keywords in keywords_data.items():
        for word, count in keywords.items():
            all_data.append({
                "Kategoria": category,
                "Słowo kluczowe": word,
                "Liczba wystąpień": count
            })
    
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values(["Kategoria", "Liczba wystąpień"], ascending=[True, False])
        
        print(f"\n=== {title} ===")
        print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
        return df
    else:
        print(f"\n=== {title} ===")
        print("Brak danych do wyświetlenia.")
        return pd.DataFrame()

def save_report_to_csv(df, filename=None):
    """Zapisuje raport do pliku CSV."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raport_analizy_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"📊 Raport zapisany: {filename}")
    return filename

def save_report_to_json(data, filename=None):
    """Zapisuje raport do pliku JSON."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raport_analizy_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Raport JSON zapisany: {filename}")
    return filename 