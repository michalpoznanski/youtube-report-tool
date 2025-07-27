#!/usr/bin/env python3
"""
AI Name Classifier - Inteligentna klasyfikacja nazwisk
Automatycznie rozpoznaje prawdziwe nazwiska vs nazwy programów vs firmy
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pandas as pd
from datetime import datetime

class AINameClassifier:
    def __init__(self):
        self.name_patterns = self._load_linguistic_patterns()
        self.context_weights = self._define_context_weights()
        self.classification_cache = {}
        
    def _load_linguistic_patterns(self) -> Dict:
        """Wzorce językowe dla różnych typów nazw"""
        return {
            'person_indicators': [
                # Kontekst osoby
                'gościem', 'wywiad z', 'rozmowa z', 'gość programu',
                'minister', 'poseł', 'posłanka', 'senator', 'deputowany',
                'aktor', 'aktorka', 'piosenkarz', 'piosenkarka', 'artysta',
                'reżyser', 'producent', 'dziennikarz', 'redaktor',
                'ekspert', 'analityk', 'komentator', 'publicysta',
                'prezes', 'dyrektor', 'szef', 'lider', 'przewodniczący',
                'profesor', 'doktor', 'dr', 'prof.', 'hab.',
                'mec.', 'adwokat', 'prawnik', 'sędzia',
                'o ', 'z ', 'według', 'zdaniem', 'jak mówi', 'jak twierdzi',
                'wypowiedź', 'komentarz', 'opinia', 'stanowisko'
            ],
            
            'show_format_indicators': [
                # Kontekst programu/formatu
                'program', 'audycja', 'format', 'serial', 'show', 'emisja',
                'odcinek', 'sezon', 'finał', 'premiera', 'debiut',
                'przedstawia', 'prezentuje', 'prowadzi', 'moderuje',
                'nowy program', 'nowa audycja', 'nowy format',
                'w programie', 'w audycji', 'w formacie',
                'oglądaj', 'słuchaj', 'śledź', 'subskrybuj'
            ],
            
            'company_indicators': [
                # Kontekst firmy/organizacji
                'sp. z o.o.', 'sa', 's.a.', 'spółka', 'firma', 'przedsiębiorstwo',
                'production', 'productions', 'studio', 'media', 'grupa',
                'fundacja', 'stowarzyszenie', 'organizacja', 'instytut',
                'centrum', 'agencja', 'biuro', 'kancelaria', 'wydawnictwo',
                'redakcja', 'zespół', 'ekipa', 'staff'
            ],
            
            'exclude_patterns': [
                # Wzorce do wykluczenia (nie nazwiska)
                'wielka', 'wielki', 'nowa', 'nowy', 'stara', 'stary',
                'ostatnia', 'ostatni', 'pierwsza', 'pierwszy',
                'dobra', 'dobry', 'zła', 'zły', 'lepsza', 'lepszy',
                'najnowsza', 'najnowszy', 'specjalna', 'specjalny',
                'breaking news', 'live stream', 'na żywo', 'relacja'
            ]
        }
    
    def _define_context_weights(self) -> Dict:
        """Wagi dla różnych kontekstów analizy"""
        return {
            'title_weight': 0.4,      # Tytuł filmu
            'description_weight': 0.3, # Opis
            'channel_weight': 0.2,     # Nazwa kanału
            'views_weight': 0.1        # Liczba wyświetleń
        }
    
    def analyze_name_context(self, name: str, title: str, description: str, 
                           channel: str, views: int) -> Dict:
        """Analizuje kontekst nazwy i zwraca prawdopodobieństwa"""
        
        # Przygotuj tekst do analizy
        full_text = f"{title} {description} {channel}".lower()
        
        # Sprawdź czy nazwa występuje w kontekście osoby
        person_score = self._calculate_person_score(name, full_text, views)
        
        # Sprawdź czy to nazwa programu/formatu
        format_score = self._calculate_format_score(name, full_text, views)
        
        # Sprawdź czy to firma/organizacja
        company_score = self._calculate_company_score(name, full_text, views)
        
        # Sprawdź wzorce wykluczające
        exclusion_score = self._calculate_exclusion_score(name, full_text)
        
        # Normalizuj wyniki
        total_score = person_score + format_score + company_score
        if total_score > 0:
            person_prob = (person_score / total_score) * (1 - exclusion_score)
            format_prob = (format_score / total_score) * (1 - exclusion_score)
            company_prob = (company_score / total_score) * (1 - exclusion_score)
        else:
            person_prob = format_prob = company_prob = 0
        
        return {
            'name': name,
            'probabilities': {
                'person': round(person_prob * 100, 1),
                'format': round(format_prob * 100, 1),
                'company': round(company_prob * 100, 1),
                'excluded': round(exclusion_score * 100, 1)
            },
            'classification': self._determine_classification(person_prob, format_prob, 
                                                           company_prob, exclusion_score),
            'confidence': self._calculate_confidence(person_prob, format_prob, 
                                                   company_prob, exclusion_score),
            'evidence': self._extract_evidence(name, full_text),
            'views': views,
            'context_strength': self._calculate_context_strength(full_text)
        }
    
    def _calculate_person_score(self, name: str, text: str, views: int) -> float:
        """Oblicza prawdopodobieństwo że to osoba"""
        score = 0
        
        # Sprawdź wzorce osobowe w tekście
        for pattern in self.name_patterns['person_indicators']:
            if pattern in text:
                # Sprawdź czy wzorzec występuje blisko nazwy
                if self._is_pattern_near_name(name, pattern, text):
                    score += 2.0  # Silny sygnał
                else:
                    score += 0.5  # Słaby sygnał
        
        # Bonus za strukturę imię+nazwisko
        if self._looks_like_person_name(name):
            score += 1.5
        
        # Bonus za wysokie wyświetlenia (popularne osoby)
        if views > 50000:
            score += 1.0
        elif views > 20000:
            score += 0.5
        
        return score
    
    def _calculate_format_score(self, name: str, text: str, views: int) -> float:
        """Oblicza prawdopodobieństwo że to format/program"""
        score = 0
        
        # Sprawdź wzorce formatów
        for pattern in self.name_patterns['show_format_indicators']:
            if pattern in text:
                if self._is_pattern_near_name(name, pattern, text):
                    score += 2.0
                else:
                    score += 0.5
        
        # Sprawdź charakterystyczne słowa w nazwie
        format_words = ['raport', 'debata', 'front', 'wojna', 'news', 'live', 
                       'show', 'talk', 'program', 'magazyn']
        for word in format_words:
            if word.lower() in name.lower():
                score += 1.5
        
        return score
    
    def _calculate_company_score(self, name: str, text: str, views: int) -> float:
        """Oblicza prawdopodobieństwo że to firma"""
        score = 0
        
        # Sprawdź wzorce firm
        for pattern in self.name_patterns['company_indicators']:
            if pattern in text:
                if self._is_pattern_near_name(name, pattern, text):
                    score += 2.0
                else:
                    score += 0.5
        
        # Sprawdź charakterystyczne końcówki firm
        company_endings = ['production', 'media', 'studio', 'group', 'team']
        for ending in company_endings:
            if name.lower().endswith(ending):
                score += 2.0
        
        return score
    
    def _calculate_exclusion_score(self, name: str, text: str) -> float:
        """Oblicza prawdopodobieństwo wykluczenia (nie nazwisko)"""
        score = 0
        
        for pattern in self.name_patterns['exclude_patterns']:
            if pattern in name.lower() or pattern in text:
                score += 0.3
        
        # Maksymalnie 0.9 (zostaw szansę na błąd)
        return min(score, 0.9)
    
    def _is_pattern_near_name(self, name: str, pattern: str, text: str, 
                             max_distance: int = 50) -> bool:
        """Sprawdza czy wzorzec występuje blisko nazwy"""
        name_pos = text.find(name.lower())
        pattern_pos = text.find(pattern)
        
        if name_pos != -1 and pattern_pos != -1:
            return abs(name_pos - pattern_pos) <= max_distance
        return False
    
    def _looks_like_person_name(self, name: str) -> bool:
        """Sprawdza czy nazwa wygląda jak imię+nazwisko"""
        words = name.split()
        if len(words) != 2:
            return False
        
        first, last = words
        
        # Polskie wzorce imion
        polish_name_endings = {
            'male': ['ek', 'an', 'sz', 'ł', 'r', 'k', 'w', 'j', 't', 'm', 'n'],
            'female': ['a', 'ina', 'ka', 'ła', 'ra', 'ta', 'ma', 'na', 'da', 'sa']
        }
        
        # Sprawdź czy pierwsze słowo może być imieniem
        first_lower = first.lower()
        could_be_name = any(first_lower.endswith(ending) 
                           for ending_list in polish_name_endings.values() 
                           for ending in ending_list)
        
        # Sprawdź długość
        reasonable_length = 3 <= len(first) <= 12 and 3 <= len(last) <= 15
        
        # Sprawdź czy zaczyna się wielką literą
        proper_case = first[0].isupper() and last[0].isupper()
        
        return could_be_name and reasonable_length and proper_case
    
    def _determine_classification(self, person_prob: float, format_prob: float, 
                                company_prob: float, exclusion_prob: float) -> str:
        """Określa końcową klasyfikację"""
        if exclusion_prob > 0.7:
            return 'excluded'
        
        max_prob = max(person_prob, format_prob, company_prob)
        
        if max_prob < 0.3:
            return 'unknown'
        elif person_prob == max_prob:
            return 'person'
        elif format_prob == max_prob:
            return 'format'
        else:
            return 'company'
    
    def _calculate_confidence(self, person_prob: float, format_prob: float, 
                            company_prob: float, exclusion_prob: float) -> float:
        """Oblicza pewność klasyfikacji"""
        if exclusion_prob > 0.7:
            return exclusion_prob
        
        probs = [person_prob, format_prob, company_prob]
        max_prob = max(probs)
        second_max = sorted(probs, reverse=True)[1]
        
        # Pewność = różnica między najwyższą a drugą najwyższą
        confidence = max_prob - second_max
        return round(confidence, 2)
    
    def _extract_evidence(self, name: str, text: str) -> List[str]:
        """Wyciąga dowody klasyfikacji z tekstu"""
        evidence = []
        
        # Znajdź fragmenty tekstu zawierające nazwę
        sentences = text.split('.')
        for sentence in sentences:
            if name.lower() in sentence:
                # Ogranicz długość dowodu
                if len(sentence) <= 100:
                    evidence.append(sentence.strip())
                else:
                    # Znajdź fragment wokół nazwy
                    name_pos = sentence.find(name.lower())
                    start = max(0, name_pos - 30)
                    end = min(len(sentence), name_pos + len(name) + 30)
                    evidence.append("..." + sentence[start:end] + "...")
        
        return evidence[:3]  # Maksymalnie 3 dowody
    
    def _calculate_context_strength(self, text: str) -> float:
        """Oblicza siłę kontekstu (ile informacji mamy)"""
        word_count = len(text.split())
        
        if word_count > 100:
            return 1.0  # Silny kontekst
        elif word_count > 50:
            return 0.7  # Średni kontekst
        elif word_count > 20:
            return 0.4  # Słaby kontekst
        else:
            return 0.1  # Bardzo słaby kontekst
    
    def batch_classify_candidates(self, candidates_data: Dict) -> Dict:
        """Klasyfikuje wszystkich kandydatów na raz"""
        results = {}
        
        for name, candidate_info in candidates_data.items():
            appearances = candidate_info.get('appearances', [])
            
            # Analizuj wszystkie wystąpienia
            all_analyses = []
            for appearance in appearances:
                analysis = self.analyze_name_context(
                    name,
                    appearance.get('title', ''),
                    appearance.get('description', ''),
                    appearance.get('channel', ''),
                    appearance.get('views', 0)
                )
                all_analyses.append(analysis)
            
            # Agreguj wyniki
            aggregated = self._aggregate_analyses(all_analyses)
            results[name] = aggregated
        
        return results
    
    def _aggregate_analyses(self, analyses: List[Dict]) -> Dict:
        """Agreguje wyniki analizy z wielu wystąpień"""
        if not analyses:
            return {}
        
        # Średnie prawdopodobieństwa
        avg_probs = {
            'person': sum(a['probabilities']['person'] for a in analyses) / len(analyses),
            'format': sum(a['probabilities']['format'] for a in analyses) / len(analyses),
            'company': sum(a['probabilities']['company'] for a in analyses) / len(analyses),
            'excluded': sum(a['probabilities']['excluded'] for a in analyses) / len(analyses)
        }
        
        # Najlepsza klasyfikacja
        max_prob_type = max(avg_probs.items(), key=lambda x: x[1])[0]
        
        # Agreguj dowody
        all_evidence = []
        for analysis in analyses:
            all_evidence.extend(analysis.get('evidence', []))
        
        return {
            'name': analyses[0]['name'],
            'average_probabilities': avg_probs,
            'classification': max_prob_type,
            'confidence': max(avg_probs.values()) - sorted(avg_probs.values(), reverse=True)[1],
            'total_appearances': len(analyses),
            'evidence': all_evidence[:5],  # Top 5 dowodów
            'recommendation': self._make_recommendation(avg_probs, len(analyses))
        }
    
    def _make_recommendation(self, probs: Dict, appearances: int) -> str:
        """Rekomendacja co zrobić z kandydatem"""
        max_prob = max(probs.values())
        max_type = max(probs.items(), key=lambda x: x[1])[0]
        
        if probs['excluded'] > 60:
            return 'REJECT - prawdopodobnie nie jest nazwiskiem'
        elif max_prob > 70 and max_type == 'person' and appearances >= 3:
            return 'AUTO_APPROVE - wysokie prawdopodobieństwo osoby'
        elif max_prob > 50 and max_type == 'person':
            return 'MANUAL_REVIEW - umiarkowane prawdopodobieństwo'
        else:
            return 'REJECT - niskie prawdopodobieństwo osoby'

# ===== FUNKCJE POMOCNICZE =====

def create_ai_classifier() -> AINameClassifier:
    """Tworzy i zwraca instancję AI classifiera"""
    return AINameClassifier()

def test_classifier_with_examples():
    """Testuje classifier na przykładowych danych"""
    classifier = AINameClassifier()
    
    test_cases = [
        {
            'name': 'Jan Kowalski',
            'title': 'Wywiad z Janem Kowalskim o polityce',
            'description': 'Gościem programu Jan Kowalski, minister edukacji',
            'channel': 'TVP Info',
            'views': 45000
        },
        {
            'name': 'Fronty Wojny',
            'title': 'Fronty Wojny - nowy odcinek',
            'description': 'W programie Fronty Wojny omawiamy sytuację międzynarodową',
            'channel': 'Historia TV',
            'views': 25000
        },
        {
            'name': 'Kombinat Medialny',
            'title': 'Produkcja Kombinat Medialny',
            'description': 'Wydawca: Kombinat Medialny Sp. z o.o.',
            'channel': 'SEKIELSKI',
            'views': 30000
        }
    ]
    
    print("🧠 **TEST AI NAME CLASSIFIER**\n")
    
    for i, case in enumerate(test_cases, 1):
        result = classifier.analyze_name_context(**case)
        
        print(f"**{i}. {case['name']}**")
        print(f"📊 Prawdopodobieństwa:")
        for prob_type, prob_value in result['probabilities'].items():
            print(f"   • {prob_type}: {prob_value}%")
        print(f"🎯 Klasyfikacja: **{result['classification']}**")
        print(f"✅ Pewność: {result['confidence']*100:.1f}%")
        print(f"📝 Dowody: {result['evidence'][:2]}")
        print()

if __name__ == "__main__":
    test_classifier_with_examples() 