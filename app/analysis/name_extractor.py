import re
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class NameExtractor:
    """Ekstrakcja nazwisk z tekstu"""
    
    def __init__(self):
        # Polskie nazwiska - wzorce
        self.name_patterns = [
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b',
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+-[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b',
            r'\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b'
        ]
        
        # Słowa do ignorowania
        self.ignore_words = {
            'YouTube', 'Video', 'Film', 'Kanał', 'Polska', 'Polski', 'Polskie',
            'Dzisiaj', 'Wczoraj', 'Dzisiaj', 'Teraz', 'Live', 'Stream',
            'Nowy', 'Nowa', 'Nowe', 'Najnowszy', 'Najnowsza', 'Najnowsze'
        }
    
    def extract_names(self, text: str) -> List[str]:
        """Wyciąga nazwiska z tekstu"""
        names = set()
        
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Sprawdź czy to nie jest słowo do ignorowania
                if not self._should_ignore(match):
                    normalized = self.normalize_name(match)
                    if normalized:
                        names.add(normalized)
        
        return list(names)
    
    def normalize_name(self, name: str) -> str:
        """Normalizuje polskie nazwiska"""
        # Usuń nadmiarowe spacje
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Konwertuj na małe litery i z powrotem na wielkie pierwsze
        parts = name.split()
        normalized_parts = []
        
        for part in parts:
            if part:
                # Usuń znaki specjalne na początku/końcu
                part = re.sub(r'^[^\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+', '', part)
                part = re.sub(r'[^\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+$', '', part)
                
                if part:
                    # Kapitalizuj pierwsze litery
                    part = part.lower()
                    part = part[0].upper() + part[1:]
                    normalized_parts.append(part)
        
        return ' '.join(normalized_parts)
    
    def _should_ignore(self, text: str) -> bool:
        """Sprawdza czy tekst powinien być ignorowany"""
        return text in self.ignore_words or len(text.split()) < 2
    
    def extract_from_video_data(self, video_data: dict) -> List[str]:
        """Wyciąga nazwiska z danych filmu"""
        names = set()
        
        # Z tytułu
        if 'title' in video_data:
            names.update(self.extract_names(video_data['title']))
        
        # Z opisu
        if 'description' in video_data:
            names.update(self.extract_names(video_data['description']))
        
        # Z tagów
        if 'tags' in video_data and video_data['tags']:
            for tag in video_data['tags']:
                names.update(self.extract_names(tag))
        
        return list(names) 