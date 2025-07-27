#!/usr/bin/env python3
"""
Inteligentny system uczenia się nowych nazwisk
Automatycznie wykrywa i proponuje nowe nazwiska do dodania
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

try:
    from ai_name_classifier import AINameClassifier
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI Name Classifier niedostępny - używam prostego systemu")

class SmartNameLearner:
    def __init__(self):
        self.learning_file = 'learned_names.json'
        self.candidates_file = 'name_candidates.json' 
        self.load_learned_names()
        self.load_candidates()
        
        # AI Classifier
        if AI_AVAILABLE:
            self.ai_classifier = AINameClassifier()
            print("🤖 AI Name Classifier załadowany")
        else:
            self.ai_classifier = None
    
    def load_learned_names(self):
        """Wczytuje wyuczone nazwiska"""
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                self.learned_names = json.load(f)
        except FileNotFoundError:
            self.learned_names = {
                'showbiz': [],
                'politics': [],
                'motoryzacja': [],
                'podcast': []
            }
    
    def load_candidates(self):
        """Wczytuje kandydatów na nowe nazwiska"""
        try:
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                self.candidates = json.load(f)
        except FileNotFoundError:
            self.candidates = {}
    
    def save_learned_names(self):
        """Zapisuje wyuczone nazwiska"""
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(self.learned_names, f, indent=2, ensure_ascii=False)
    
    def save_candidates(self):
        """Zapisuje kandydatów"""
        with open(self.candidates_file, 'w', encoding='utf-8') as f:
            json.dump(self.candidates, f, indent=2, ensure_ascii=False)
    
    def is_potential_name(self, text: str) -> bool:
        """Sprawdza czy tekst może być nazwiskiem"""
        if not text or len(text) < 4:
            return False
            
        # Wzorzec: Imię Nazwisko (2-3 słowa, wielkie litery)
        pattern = r'^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(\-[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)?$'
        if not re.match(pattern, text):
            return False
        
        # Blacklista słów które nie są nazwiskami
        blacklist = [
            # Media i platformy
            'YouTube', 'Google', 'Facebook', 'Instagram', 'Twitter', 'TikTok',
            'Radio ZET', 'Polsat News', 'TVP Info', 'Wirtualna Polska', 
            'Big Tech', 'Sztuczna Inteligencja', 'Machine Learning',
            
            # Znani międzynarodowi (nie polscy)
            'Donald Trump', 'Joe Biden', 'Vladimir Putin', 'Elon Musk',
            'Władimir Putin', 'Joe Biden', 'Xi Jinping', 'Angela Merkel',
            
            # Miejsca
            'Nowy Jork', 'Los Angeles', 'Stany Zjednoczone', 'Wielka Brytania',
            'Nowa Zelandia', 'Nowa Hiszpania', 'Nowy Orlean',
            
            # Nazwy programów i formatów - GŁÓWNY PROBLEM!
            'Raportu Międzynarodowego', 'Fronty Wojny', 'Nowa Polityka',
            'Wielka Debata', 'Ostatnia Szansa', 'Pierwsza Miłość', 'Nowy Dzień',
            'Wielki Test', 'Ostatni Raport', 'Nowa Era', 'Wielka Ucieczka',
            'Stara Miłość', 'Nowe Życie', 'Wielka Historia', 'Ostatni Taniec',
            'Nowa Nadzieja', 'Wielka Przygoda', 'Stary Przyjaciel',
            'Nowy Początek', 'Wielka Podróż', 'Ostatnia Wola', 'Nowa Polska',
            'Wielka Polska', 'Stara Polska', 'Nowa Europa', 'Wielka Europa',
            
            # Tytuły i formaty medialne
            'Film Review', 'Movie Trailer', 'Music Video', 'News Report',
            'Pierwszy Raz', 'Nowy Album', 'Ostatni Film', 'Wielka Gala',
            'Nowa Płyta', 'Pierwszy Koncert', 'Ostatnia Debata',
            'Breaking News', 'Special Report', 'Live Stream', 'Press Conference',
            
            # Typowe zwroty które mogą być błędnie wykryte
            'Bardzo Ważne', 'Niezwykle Ważny', 'Ostatni Moment', 'Pierwszy Dzień',
            'Wielki Sukces', 'Nowa Szansa', 'Ostatnia Chwila', 'Pierwszy Krok',
            'Nowa Rzeczywistość', 'Wielka Zmiana', 'Stare Problemy', 'Nowe Wyzwania',
            
            # Abstrakty i pojęcia
            'Sztuczna Inteligencja', 'Machine Learning', 'Deep Learning',
            'Virtual Reality', 'Augmented Reality', 'Internet Things',
            'Social Media', 'Digital Marketing', 'Content Creator'
        ]
        
        for excluded in blacklist:
            if excluded.lower() in text.lower():
                return False
        
        # Dodatkowa walidacja czy to rzeczywiście nazwisko osoby
        if not self.looks_like_person_name(text):
            return False
        
        return True
    
    def looks_like_person_name(self, text: str) -> bool:
        """Dodatkowa walidacja czy to rzeczywiście nazwisko osoby"""
        words = text.split()
        if len(words) != 2:
            return False
            
        first_word, second_word = words
        
        # Sprawdź czy pierwsze słowo może być imieniem
        # Typowe polskie imiona męskie i żeńskie wzorce
        typical_name_endings = [
            # Męskie
            'ek', 'an', 'sz', 'ł', 'r', 'k', 'w', 'j', 't', 'm', 'n',
            # Żeńskie  
            'a', 'ina', 'ka', 'ła', 'ra', 'ta', 'ma', 'na', 'da', 'sa'
        ]
        
        # Sprawdź czy końcówka pierwszego słowa wygląda jak imię
        name_like = any(first_word.lower().endswith(ending) for ending in typical_name_endings)
        
        # Sprawdź długość - imiona zwykle 3-12 liter
        name_length_ok = 3 <= len(first_word) <= 12 and 3 <= len(second_word) <= 15
        
        # Wyklucz typowe słowa które nie są imionami
        not_names = [
            'Wielka', 'Wielki', 'Nowa', 'Nowy', 'Stara', 'Stary', 
            'Ostatnia', 'Ostatni', 'Pierwsza', 'Pierwszy', 'Dobra', 'Dobry',
            'Mała', 'Mały', 'Duża', 'Duży', 'Bardzo', 'Niezwykle',
            'Całkowita', 'Całkowity', 'Kompletna', 'Kompletny'
        ]
        
        is_not_adjective = first_word not in not_names
        
        return name_like and name_length_ok and is_not_adjective
    
    def ai_classify_name(self, name: str, title: str, description: str, channel: str, views: int) -> Dict:
        """Klasyfikuje nazwę używając AI (jeśli dostępne)"""
        if self.ai_classifier:
            return self.ai_classifier.analyze_name_context(name, title, description, channel, views)
        else:
            # Fallback na prosty system
            return {
                'name': name,
                'classification': 'unknown',
                'probabilities': {'person': 50.0, 'format': 25.0, 'company': 25.0, 'excluded': 0.0},
                'confidence': 0.1,
                'evidence': [],
                'ai_used': False
            }
    
    def batch_ai_classify_candidates(self) -> Dict:
        """Klasyfikuje wszystkich kandydatów używając AI"""
        if not self.ai_classifier:
            return {}
        
        return self.ai_classifier.batch_classify_candidates(self.candidates)
    
    def auto_process_ai_candidates(self) -> Dict:
        """Automatycznie przetwarza kandydatów na podstawie AI"""
        if not self.ai_classifier:
            return {'processed': 0, 'approved': 0, 'rejected': 0}
        
        ai_results = self.batch_ai_classify_candidates()
        
        processed = 0
        approved = 0
        rejected = 0
        
        for name, ai_result in ai_results.items():
            recommendation = ai_result.get('recommendation', '')
            
            if 'AUTO_APPROVE' in recommendation:
                # Automatycznie akceptuj
                category = ai_result.get('classification', 'showbiz')
                if category == 'person':
                    # Określ kategorię na podstawie kontekstu
                    category = self.detect_category_from_context(
                        name, 
                        ai_result.get('evidence', [''])[0], 
                        '', 
                        ''
                    )
                self.approve_name(name, category)
                approved += 1
                
            elif 'REJECT' in recommendation:
                # Automatycznie odrzuć
                self.reject_name(name)
                rejected += 1
                
            processed += 1
        
        return {
            'processed': processed,
            'approved': approved,
            'rejected': rejected,
            'ai_results': ai_results
        }
    
    def detect_category_from_context(self, name: str, title: str, description: str, channel: str) -> str:
        """Wykrywa kategorię nazwiska na podstawie kontekstu"""
        context = f"{title} {description} {channel}".lower()
        
        scores = {
            'politics': 0,
            'showbiz': 0,
            'motoryzacja': 0,
            'podcast': 0
        }
        
        # Słowa kluczowe z wagami
        political_keywords = ['wybory', 'rząd', 'minister', 'sejm', 'prezydent', 'partia', 'polityk', 'kampania', 'debata', 'afera', 'prokuratura']
        showbiz_keywords = ['muzyka', 'film', 'aktor', 'piosenkarz', 'gwiazda', 'celebryta', 'koncert', 'album', 'teledysk', 'premiera', 'gala']
        motor_keywords = ['samochód', 'auto', 'wyścig', 'rally', 'formuła', 'silnik', 'test drive', 'motoryzacja', 'tor', 'drift']
        podcast_keywords = ['podcast', 'wywiad', 'rozmowa', 'gość', 'audio', 'radio', 'talk show', 'dyskusja']
        
        for keyword in political_keywords:
            if keyword in context:
                scores['politics'] += 2
        
        for keyword in showbiz_keywords:
            if keyword in context:
                scores['showbiz'] += 2
                
        for keyword in motor_keywords:
            if keyword in context:
                scores['motoryzacja'] += 2
                
        for keyword in podcast_keywords:
            if keyword in context:
                scores['podcast'] += 2
        
        # Kontekst kanału (większa waga)
        if any(word in channel.lower() for word in ['polsat', 'tvp', 'rmf', 'tok fm', 'polityka']):
            scores['politics'] += 3
            
        if any(word in channel.lower() for word in ['muzyka', 'film', 'gwiazdy', 'celebryta', 'showbiz']):
            scores['showbiz'] += 3
            
        if any(word in channel.lower() for word in ['auto', 'motor', 'samochód', 'wyścig']):
            scores['motoryzacja'] += 3
            
        if any(word in channel.lower() for word in ['podcast', 'rozmowa', 'wywiad']):
            scores['podcast'] += 3
        
        # Zwróć kategorię z najwyższym wynikiem
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'showbiz'  # domyślnie
    
    def add_candidate(self, name: str, title: str, description: str, channel: str, views: int, suggested_category: str = None) -> bool:
        """Dodaje kandydata na nowe nazwisko"""
        if not self.is_potential_name(name):
            return False
        
        # Automatycznie wykryj kategorię jeśli nie podano
        if not suggested_category:
            suggested_category = self.detect_category_from_context(name, title, description, channel)
        
        # Dodaj do kandydatów
        if name not in self.candidates:
            self.candidates[name] = {
                'appearances': [],
                'suggested_category': suggested_category,
                'confidence_score': 0
            }
        
        # Dodaj nowe wystąpienie
        self.candidates[name]['appearances'].append({
            'title': title,
            'description': description[:200],
            'channel': channel,
            'views': views,
            'category': suggested_category,
            'timestamp': datetime.now().isoformat()
        })
        
        # Aktualizuj score
        appearances = len(self.candidates[name]['appearances'])
        total_views = sum(app['views'] for app in self.candidates[name]['appearances'])
        
        # Score: wystąpienia (60%) + wyświetlenia (40%)
        view_score = min(total_views / 100000, 1.0)  # Normalizacja do 100K views = 1.0
        self.candidates[name]['confidence_score'] = (appearances * 0.6 + view_score * 0.4) * 100
        
        self.save_candidates()
        return True
    
    def get_top_candidates(self, limit: int = 20, min_score: float = 30.0) -> List[Dict]:
        """Zwraca top kandydatów do akceptacji"""
        candidates_list = []
        
        for name, data in self.candidates.items():
            if data['confidence_score'] >= min_score:
                candidates_list.append({
                    'name': name,
                    'score': round(data['confidence_score'], 1),
                    'appearances': len(data['appearances']),
                    'suggested_category': data['suggested_category'],
                    'total_views': sum(app['views'] for app in data['appearances']),
                    'channels': list(set(app['channel'] for app in data['appearances'])),
                    'recent_titles': [app['title'] for app in data['appearances'][-3:]]  # 3 ostatnie tytuły
                })
        
        candidates_list.sort(key=lambda x: x['score'], reverse=True)
        return candidates_list[:limit]
    
    def approve_name(self, name: str, category: str) -> bool:
        """Akceptuje nazwisko i dodaje do wyuczonych"""
        if name in self.candidates:
            if category in self.learned_names:
                self.learned_names[category].append(name)
                del self.candidates[name]
                self.save_learned_names()
                self.save_candidates()
                return True
        return False
    
    def reject_name(self, name: str) -> bool:
        """Odrzuca nazwisko i dodaje do blacklisty"""
        if name in self.candidates:
            del self.candidates[name]
            self.save_candidates()
            return True
        return False
    
    def get_all_learned_names(self) -> Dict:
        """Zwraca wszystkie wyuczone nazwiska"""
        return self.learned_names.copy()
    
    def get_candidate_details(self, name: str) -> Optional[Dict]:
        """Zwraca szczegóły kandydata"""
        return self.candidates.get(name)
    
    def cleanup_old_candidates(self, days_old: int = 30):
        """Usuwa starych kandydatów z niskim score"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        to_remove = []
        
        for name, data in self.candidates.items():
            if data['confidence_score'] < 20:  # Niski score
                latest_appearance = max(data['appearances'], key=lambda x: x['timestamp'])
                appearance_date = datetime.fromisoformat(latest_appearance['timestamp'])
                
                if appearance_date < cutoff_date:
                    to_remove.append(name)
        
        for name in to_remove:
            del self.candidates[name]
        
        if to_remove:
            self.save_candidates()
            
        return len(to_remove)

# Przykład użycia
if __name__ == "__main__":
    learner = SmartNameLearner()
    
    # Test dodawania kandydata
    learner.add_candidate(
        "Jan Kowalski",
        "Jan Kowalski o sytuacji politycznej w Polsce",
        "Wywiad z politykiem o aktualnej sytuacji", 
        "Polsat News",
        50000
    )
    
    print("Top kandydaci:")
    for candidate in learner.get_top_candidates(5):
        print(f"- {candidate['name']} ({candidate['score']:.1f}%) - {candidate['suggested_category']}") 