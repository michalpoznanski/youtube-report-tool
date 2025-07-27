#!/usr/bin/env python3
"""
Name Normalizer - Normalizacja polskich nazwisk
Konwertuje odmiany nazwisk do formy podstawowej "Imię Nazwisko"
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class PolishNameNormalizer:
    def __init__(self):
        self.surname_endings = self._load_polish_surname_patterns()
        self.name_endings = self._load_polish_name_patterns()
        self.normalized_cache = {}
        
    def _load_polish_surname_patterns(self) -> Dict:
        """Wzorce końcówek polskich nazwisk w różnych przypadkach"""
        return {
            # Męskie nazwiska
            'male_surnames': {
                'base_endings': ['ski', 'cki', 'dzki', 'wski', 'owski', 'ewski', 'ański', 'iński'],
                'declined_endings': ['skiego', 'ckiego', 'dzkiego', 'wskiego', 'owskiego', 'ewskiego', 'ańskiego', 'ińskiego',
                                   'skiemu', 'ckiemu', 'dzkiemu', 'wskiemu', 'owskiemu', 'ewskiemu', 'ańskiemu', 'ińskiemu',
                                   'skim', 'ckim', 'dzkim', 'wskim', 'owskim', 'ewskim', 'ańskim', 'ińskim'],
                'mapping': {
                    # -skiego -> -ski
                    'skiego': 'ski', 'ckiego': 'cki', 'dzkiego': 'dzki', 'wskiego': 'wski',
                    'owskiego': 'owski', 'ewskiego': 'ewski', 'ańskiego': 'ański', 'ińskiego': 'iński',
                    # -skiemu -> -ski  
                    'skiemu': 'ski', 'ckiemu': 'cki', 'dzkiemu': 'dzki', 'wskiemu': 'wski',
                    'owskiemu': 'owski', 'ewskiemu': 'ewski', 'ańskiemu': 'ański', 'ińskiemu': 'iński',
                    # -skim -> -ski
                    'skim': 'ski', 'ckim': 'cki', 'dzkim': 'dzki', 'wskim': 'wski',
                    'owskim': 'owski', 'ewskim': 'ewski', 'ańskim': 'ański', 'ińskim': 'iński'
                }
            },
            
            # Żeńskie nazwiska
            'female_surnames': {
                'base_endings': ['ska', 'cka', 'dzka', 'wska', 'owska', 'ewska', 'ańska', 'ińska'],
                'declined_endings': ['skiej', 'ckiej', 'dzkiej', 'wskiej', 'owskiej', 'ewskiej', 'ańskiej', 'ińskiej'],
                'mapping': {
                    'skiej': 'ska', 'ckiej': 'cka', 'dzkiej': 'dzka', 'wskiej': 'wska',
                    'owskiej': 'owska', 'ewskiej': 'ewska', 'ańskiej': 'ańska', 'ińskiej': 'ińska'
                }
            },
            
            # Inne wzorce
            'other_patterns': {
                'mapping': {
                    # Typowe końcówki
                    'a': '', 'owi': '', 'em': '', 'ie': '', 'u': '',
                                         # Specjalne przypadki
                     'tuska': 'tusk', 'tuskiem': 'tusk', 'tuskowi': 'tusk', 'tusku': 'tusk',
                     'dudy': 'duda', 'dudą': 'duda', 'dudzie': 'duda', 'dude': 'duda',
                     'morawiecki': 'morawiecki', 'morawieckiego': 'morawiecki', 'morawieckim': 'morawiecki',
                     # Poprawka dla -em
                     'iem': '', 'em': '', 'ym': ''
                }
            }
        }
    
    def _load_polish_name_patterns(self) -> Dict:
        """Wzorce końcówek polskich imion w różnych przypadkach"""
        return {
            'male_names': {
                'mapping': {
                    # Popularne męskie imiona
                    'donalda': 'donald', 'donaldem': 'donald', 'donaldowi': 'donald', 'donaldzie': 'donald',
                    'andrzeja': 'andrzej', 'andrzejem': 'andrzej', 'andrzejowi': 'andrzej', 'andrzeju': 'andrzej',
                    'mateusza': 'mateusz', 'mateuszem': 'mateusz', 'mateuszowi': 'mateusz', 'mateuszu': 'mateusz',
                    'jarosława': 'jarosław', 'jarosławem': 'jarosław', 'jarosławowi': 'jarosław', 'jarosławie': 'jarosław',
                    'rafała': 'rafał', 'rafałem': 'rafał', 'rafałowi': 'rafał', 'rafale': 'rafał',
                    'przemysława': 'przemysław', 'przemysławem': 'przemysław', 'przemysławowi': 'przemysław',
                    'tomasz': 'tomasz', 'tomaszem': 'tomasz', 'tomaszowi': 'tomasz', 'tomaszu': 'tomasz',
                    'marcin': 'marcin', 'marcina': 'marcin', 'marcinem': 'marcin', 'marcinowi': 'marcin',
                    'adam': 'adam', 'adama': 'adam', 'adamem': 'adam', 'adamowi': 'adam', 'adamie': 'adam'
                }
            },
            'female_names': {
                'mapping': {
                    # Popularne żeńskie imiona
                    'beaty': 'beata', 'beatą': 'beata', 'beacie': 'beata', 'beato': 'beata',
                    'ewy': 'ewa', 'ewą': 'ewa', 'ewie': 'ewa', 'ewo': 'ewa',
                    'agnieszki': 'agnieszka', 'agnieszką': 'agnieszka', 'agnieszce': 'agnieszka',
                    'katarzyny': 'katarzyna', 'katarzyną': 'katarzyna', 'katarzynie': 'katarzyna',
                    'małgorzaty': 'małgorzata', 'małgorzatą': 'małgorzata', 'małgorzacie': 'małgorzata',
                    'barbary': 'barbara', 'barbarą': 'barbara', 'barbarze': 'barbara',
                    'joanny': 'joanna', 'joanną': 'joanna', 'joannie': 'joanna'
                }
            }
        }
    
    def normalize_name_part(self, name_part: str, is_surname: bool = False) -> str:
        """Normalizuje pojedynczą część nazwiska (imię lub nazwisko)"""
        name_lower = name_part.lower()
        
        if is_surname:
            # Normalizuj nazwisko
            
            # Sprawdź męskie nazwiska
            for ending, base in self.surname_endings['male_surnames']['mapping'].items():
                if name_lower.endswith(ending):
                    return name_part[:-len(ending)] + base
            
            # Sprawdź żeńskie nazwiska  
            for ending, base in self.surname_endings['female_surnames']['mapping'].items():
                if name_lower.endswith(ending):
                    return name_part[:-len(ending)] + base
            
            # Sprawdź inne wzorce
            for declined, base in self.surname_endings['other_patterns']['mapping'].items():
                if name_lower == declined:
                    return base.title() if base else name_part
                elif name_lower.endswith(declined) and len(declined) > 1:
                    return name_part[:-len(declined)] + base if base else name_part[:-len(declined)]
        
        else:
            # Normalizuj imię
            all_name_mappings = {**self.name_endings['male_names']['mapping'], 
                               **self.name_endings['female_names']['mapping']}
            
            if name_lower in all_name_mappings:
                return all_name_mappings[name_lower].title()
        
        return name_part
    
    def normalize_full_name(self, full_name: str) -> str:
        """Normalizuje pełne nazwisko do formy 'Imię Nazwisko'"""
        
        # Cache check
        if full_name in self.normalized_cache:
            return self.normalized_cache[full_name]
        
        # Wyczyść nazwisko
        cleaned = re.sub(r'[^\w\s\-]', '', full_name).strip()
        words = cleaned.split()
        
        if len(words) == 0:
            return full_name
        
        elif len(words) == 1:
            # Samo nazwisko - spróbuj znormalizować
            normalized = self.normalize_name_part(words[0], is_surname=True)
            result = normalized.title()
            
        elif len(words) == 2:
            # Imię + Nazwisko - idealne
            first_name = self.normalize_name_part(words[0], is_surname=False)
            last_name = self.normalize_name_part(words[1], is_surname=True)
            result = f"{first_name.title()} {last_name.title()}"
            
        else:
            # Więcej słów - weź pierwsze jako imię, ostatnie jako nazwisko
            first_name = self.normalize_name_part(words[0], is_surname=False)
            last_name = self.normalize_name_part(words[-1], is_surname=True)
            result = f"{first_name.title()} {last_name.title()}"
        
        # Cache result
        self.normalized_cache[full_name] = result
        return result
    
    def group_name_variants(self, names_list: List[str]) -> Dict[str, List[str]]:
        """Grupuje różne odmiany tego samego nazwiska"""
        groups = defaultdict(list)
        
        for name in names_list:
            normalized = self.normalize_full_name(name)
            groups[normalized].append(name)
        
        return dict(groups)
    
    def get_surname_key(self, full_name: str) -> str:
        """Zwraca klucz nazwiska do grupowania (samo nazwisko)"""
        normalized = self.normalize_full_name(full_name)
        words = normalized.split()
        
        if len(words) >= 2:
            return words[-1].lower()  # Ostatnie słowo jako nazwisko
        else:
            return normalized.lower()
    
    def merge_name_statistics(self, name_stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """Łączy statystyki dla różnych odmian tego samego nazwiska"""
        
        # Grupuj według znormalizowanych nazw
        normalized_groups = defaultdict(list)
        
        for name, stats in name_stats.items():
            normalized = self.normalize_full_name(name)
            normalized_groups[normalized].append((name, stats))
        
        # Merguj statystyki
        merged_stats = {}
        
        for normalized_name, variants in normalized_groups.items():
            if len(variants) == 1:
                # Tylko jedna odmiana
                original_name, stats = variants[0]
                merged_stats[normalized_name] = stats
            else:
                # Wiele odmian - merguj
                merged = {
                    'count': 0,
                    'total_views': 0,
                    'channels': set(),
                    'videos': [],
                    'variants': []
                }
                
                for original_name, stats in variants:
                    merged['count'] += stats.get('count', 0)
                    merged['total_views'] += stats.get('total_views', 0)
                    merged['channels'].update(stats.get('channels', []))
                    merged['videos'].extend(stats.get('videos', []))
                    merged['variants'].append(original_name)
                
                # Konwertuj set z powrotem na listę
                merged['channels'] = list(merged['channels'])
                
                merged_stats[normalized_name] = merged
        
        return merged_stats

# Test funkcji
def test_normalizer():
    """Testuje normalizer na przykładach"""
    normalizer = PolishNameNormalizer()
    
    test_cases = [
        "Donald Tusk",
        "Donalda Tuska", 
        "Donaldem Tuskiem",
        "Donaldowi Tuskowi",
        "Tusk",
        "Tuska",
        "Andrzej Duda",
        "Andrzeja Dudy",
        "Dudą",
        "Mateusz Morawiecki",
        "Mateusza Morawieckiego",
        "Morawieckim",
        "Beata Szydło",
        "Beaty Szydło",
        "Szydło"
    ]
    
    print("🔄 **TEST NORMALIZATORA NAZWISK**\n")
    
    for name in test_cases:
        normalized = normalizer.normalize_full_name(name)
        surname_key = normalizer.get_surname_key(name)
        print(f"'{name}' → '{normalized}' (klucz: {surname_key})")
    
    print("\n📊 **GRUPOWANIE:**")
    groups = normalizer.group_name_variants(test_cases)
    for normalized, variants in groups.items():
        print(f"**{normalized}**: {variants}")

if __name__ == "__main__":
    test_normalizer() 