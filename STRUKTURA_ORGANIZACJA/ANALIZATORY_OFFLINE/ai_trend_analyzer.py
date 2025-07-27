#!/usr/bin/env python3
"""
System AI do analizy trendów nazwisk offline - BEZ użycia quota
"""

import os
import json
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple

class AITrendAnalyzer:
    def __init__(self):
        self.trending_names = []
        self.name_patterns = {}
        self.category_keywords = {
            'showbiz': ['gwiazda', 'celebryta', 'aktor', 'aktorka', 'piosenkarz', 'piosenkarka', 
                       'influencer', 'youtuber', 'tiktoker', 'instagram', 'media', 'rozrywka',
                       'film', 'muzyka', 'teatr', 'scena', 'show', 'program', 'wywiad', 'gala']
        }
    
    def load_existing_data(self) -> pd.DataFrame:
        """Wczytuje istniejące dane z CSV"""
        try:
            # Znajdź najnowszy plik CSV
            csv_files = [f for f in os.listdir('.') if f.startswith('youtube_data_') and f.endswith('.csv')]
            if not csv_files:
                return pd.DataFrame()
            
            latest_file = max(csv_files)
            df = pd.read_csv(latest_file, encoding='utf-8')
            print(f"📊 Załadowano {len(df)} filmów z {latest_file}")
            return df
        except Exception as e:
            print(f"❌ Błąd wczytywania danych: {e}")
            return pd.DataFrame()
    
    def extract_name_patterns(self, df: pd.DataFrame) -> Dict:
        """Analizuje wzorce nazwisk z istniejących danych"""
        patterns = {
            'common_surnames': [],
            'name_frequency': {},
            'context_keywords': {},
            'trending_patterns': {}
        }
        
        # Zbierz wszystkie nazwiska
        all_names = []
        for names_str in df['Names_Extracted'].dropna():
            if names_str:
                names = [name.strip() for name in names_str.split(',') if name.strip()]
                all_names.extend(names)
        
        # Analizuj częstotliwość
        name_counter = Counter(all_names)
        patterns['name_frequency'] = dict(name_counter.most_common(50))
        
        # Analizuj kontekst (tytuły i opisy)
        for _, row in df.iterrows():
            title = str(row['Title']).lower()
            description = str(row['Description']).lower()
            
            # Znajdź nazwiska w kontekście
            for name in name_counter.keys():
                if name.lower() in title or name.lower() in description:
                    # Wyciągnij słowa kluczowe wokół nazwiska
                    context = self.extract_context(title + ' ' + description, name.lower())
                    if context:
                        if name not in patterns['context_keywords']:
                            patterns['context_keywords'][name] = []
                        patterns['context_keywords'][name].extend(context)
        
        # Znajdź wzorce trendów (nazwiska które pojawiają się coraz częściej)
        patterns['trending_patterns'] = self.analyze_trending_patterns(df)
        
        return patterns
    
    def extract_context(self, text: str, name: str) -> List[str]:
        """Wyciąga słowa kluczowe wokół nazwiska"""
        context = []
        
        # Znajdź pozycję nazwiska w tekście
        pos = text.find(name)
        if pos != -1:
            # Weź 10 słów przed i po nazwisku
            words = text.split()
            name_pos = -1
            
            for i, word in enumerate(words):
                if name in word:
                    name_pos = i
                    break
            
            if name_pos != -1:
                start = max(0, name_pos - 5)
                end = min(len(words), name_pos + 6)
                context_words = words[start:end]
                
                # Filtruj słowa kluczowe
                for word in context_words:
                    if len(word) > 3 and word not in ['the', 'and', 'or', 'but', 'for', 'with', 'from']:
                        context.append(word)
        
        return context
    
    def analyze_trending_patterns(self, df: pd.DataFrame) -> Dict:
        """Analizuje wzorce trendów w czasie"""
        trends = {}
        
        # Grupuj dane według daty
        df['Date'] = pd.to_datetime(df['Date_of_Publishing'])
        df_sorted = df.sort_values('Date')
        
        # Analizuj nazwiska w oknach czasowych
        window_size = 2  # dni
        
        # Bezpieczne wyciąganie nazwisk
        all_names = []
        for names_str in df['Names_Extracted'].dropna():
            if isinstance(names_str, str) and names_str.strip():
                names = [name.strip() for name in names_str.split(',') if name.strip()]
                all_names.extend(names)
        
        unique_names = list(set(all_names))
        
        for name in unique_names:
            if not name or pd.isna(name):
                continue
            
            name_trend = []
            
            # Sprawdź częstotliwość w oknach czasowych
            for i in range(0, len(df_sorted), window_size):
                window_data = df_sorted.iloc[i:i+window_size]
                count = 0
                
                for _, row in window_data.iterrows():
                    if pd.notna(row['Names_Extracted']) and isinstance(row['Names_Extracted'], str):
                        names_in_row = [n.strip() for n in row['Names_Extracted'].split(',')]
                        if name in names_in_row:
                            count += 1
                
                name_trend.append(count)
            
            # Sprawdź czy trend rośnie
            if len(name_trend) >= 3:
                recent_avg = np.mean(name_trend[-3:])
                earlier_avg = np.mean(name_trend[:-3]) if len(name_trend) > 3 else 0
                
                if recent_avg > earlier_avg * 1.5:  # 50% wzrost
                    trends[name] = {
                        'trend_direction': 'up',
                        'growth_rate': (recent_avg - earlier_avg) / max(earlier_avg, 1),
                        'recent_frequency': recent_avg
                    }
        
        return trends
    
    def suggest_new_names(self, df: pd.DataFrame) -> List[Dict]:
        """Sugeruje nowe nazwiska na podstawie analizy offline"""
        suggestions = []
        
        # Analizuj wzorce
        patterns = self.extract_name_patterns(df)
        
        # Sprawdź czy są jakieś nazwiska
        if not patterns['name_frequency']:
            print("⚠️  Brak nazwisk w danych. Uruchom `!zbierz_dane` aby zebrać dane z nazwiskami.")
            return []
        
        # Znajdź nazwiska które mogą być showbiz
        for name, frequency in patterns['name_frequency'].items():
            if frequency >= 2:  # Minimum 2 wystąpienia
                score = self.calculate_showbiz_score(name, patterns, df)
                
                if score > 0.6:  # Próg dla sugestii
                    suggestions.append({
                        'name': name,
                        'score': score,
                        'frequency': frequency,
                        'reason': self.get_suggestion_reason(name, patterns, score),
                        'context': patterns['context_keywords'].get(name, [])[:5]
                    })
        
        # Sortuj według score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return suggestions[:10]  # Top 10 sugestii
    
    def calculate_showbiz_score(self, name: str, patterns: Dict, df: pd.DataFrame) -> float:
        """Oblicza score jak bardzo nazwisko pasuje do showbiz"""
        score = 0.0
        
        # 1. Częstotliwość (30%)
        frequency = patterns['name_frequency'].get(name, 0)
        score += min(frequency / 10, 1.0) * 0.3
        
        # 2. Kontekst (40%)
        context_words = patterns['context_keywords'].get(name, [])
        showbiz_matches = sum(1 for word in context_words if word in self.category_keywords['showbiz'])
        score += min(showbiz_matches / 5, 1.0) * 0.4
        
        # 3. Trend (20%)
        trend_info = patterns['trending_patterns'].get(name, {})
        if trend_info.get('trend_direction') == 'up':
            score += min(trend_info.get('growth_rate', 0), 1.0) * 0.2
        
        # 4. Wzorzec nazwiska (10%)
        if self.is_polish_name(name):
            score += 0.1
        
        return min(score, 1.0)
    
    def is_polish_name(self, name: str) -> bool:
        """Sprawdza czy nazwisko wygląda na polskie"""
        polish_endings = ['ski', 'ska', 'cki', 'cka', 'wicz', 'owicz', 'ak', 'ek', 'ik', 'yk']
        name_lower = name.lower()
        
        for ending in polish_endings:
            if name_lower.endswith(ending):
                return True
        
        return False
    
    def get_suggestion_reason(self, name: str, patterns: Dict, score: float) -> str:
        """Generuje powód sugestii"""
        reasons = []
        
        frequency = patterns['name_frequency'].get(name, 0)
        if frequency >= 5:
            reasons.append(f"Wysoka częstotliwość ({frequency} wystąpień)")
        
        context_words = patterns['context_keywords'].get(name, [])
        showbiz_words = [word for word in context_words if word in self.category_keywords['showbiz']]
        if showbiz_words:
            reasons.append(f"Kontekst showbiz: {', '.join(showbiz_words[:3])}")
        
        trend_info = patterns['trending_patterns'].get(name, {})
        if trend_info.get('trend_direction') == 'up':
            growth = trend_info.get('growth_rate', 0)
            reasons.append(f"Trend wzrostowy (+{growth:.1%})")
        
        if self.is_polish_name(name):
            reasons.append("Polskie nazwisko")
        
        return '; '.join(reasons) if reasons else "Wysoki score AI"
    
    def save_suggestions(self, suggestions: List[Dict]):
        """Zapisuje sugestie do pliku"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"ai_name_suggestions_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Sugestie AI zapisane do: {filename}")
        return filename

def main():
    """Główna funkcja"""
    analyzer = AITrendAnalyzer()
    
    # Wczytaj istniejące dane
    df = analyzer.load_existing_data()
    if df.empty:
        print("❌ Brak danych do analizy")
        return
    
    print("🤖 AI analizuje wzorce nazwisk...")
    
    # Generuj sugestie
    suggestions = analyzer.suggest_new_names(df)
    
    if suggestions:
        print(f"\n✅ AI znalazło {len(suggestions)} potencjalnych nazwisk showbiz:")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. **{suggestion['name']}** (Score: {suggestion['score']:.2f})")
            print(f"   Częstotliwość: {suggestion['frequency']} wystąpień")
            print(f"   Powód: {suggestion['reason']}")
            if suggestion['context']:
                print(f"   Kontekst: {', '.join(suggestion['context'])}")
        
        # Zapisz sugestie
        analyzer.save_suggestions(suggestions)
    else:
        print("❌ AI nie znalazło nowych nazwisk do sugestii")
        print("💡 **Następne kroki:**")
        print("   1. Uruchom `!zbierz_dane` aby zebrać dane z nazwiskami")
        print("   2. Uruchom `!nazwiska_showbiz` aby wyciągnąć nazwiska")
        print("   3. Spróbuj ponownie `!znajdz_kanały`")

if __name__ == "__main__":
    main() 