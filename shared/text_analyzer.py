import re
from collections import Counter

# spaCy wyłączone - używamy tylko wzorców
nlp = None
print("✅ Analiza bez spaCy - szybsze działanie")

# Polskie stopwords
POLISH_STOPWORDS = {
    'i', 'oraz', 'oraz', 'a', 'ale', 'lecz', 'jednak', 'jednakże', 'natomiast',
    'zaś', 'więc', 'zatem', 'dlatego', 'przeto', 'zatem', 'więc', 'zatem',
    'więc', 'zatem', 'więc', 'zatem', 'więc', 'zatem', 'więc', 'zatem',
    'w', 'na', 'z', 'do', 'od', 'przez', 'nad', 'pod', 'za', 'przed',
    'po', 'między', 'obok', 'koło', 'przy', 'u', 'bez', 'dla', 'o', 'u',
    'ten', 'ta', 'to', 'ci', 'te', 'tamten', 'tamta', 'tamto', 'tamci', 'tamte',
    'jaki', 'jaka', 'jakie', 'jacy', 'jakie', 'który', 'która', 'które', 'którzy', 'które',
    'mój', 'moja', 'moje', 'moi', 'moje', 'twój', 'twoja', 'twoje', 'twoi', 'twoje',
    'jego', 'jej', 'ich', 'nasz', 'nasza', 'nasze', 'nasi', 'nasze',
    'wasz', 'wasza', 'wasze', 'wasi', 'wasze', 'swój', 'swoja', 'swoje', 'swoi', 'swoje'
}

def clean_text(text):
    """Czyści tekst z niepotrzebnych znaków."""
    if not text:
        return ""
    
    # Usuń znaki specjalne, ale zachowaj polskie litery
    text = re.sub(r'[^\w\sąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', ' ', str(text))
    # Usuń wielokrotne spacje
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def tokenize_text(text):
    """Dzieli tekst na tokeny i usuwa stopwords."""
    if not text:
        return []
    
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    # Podziel na słowa
    tokens = cleaned.split()
    
    # Usuń stopwords i krótkie słowa
    tokens = [token for token in tokens if len(token) > 2 and token not in POLISH_STOPWORDS]
    
    return tokens

def extract_keywords_from_titles(titles, min_frequency=2):
    """Wyciąga najpopularniejsze słowa kluczowe z tytułów."""
    all_tokens = []
    
    for title in titles:
        if title:
            tokens = tokenize_text(title)
            all_tokens.extend(tokens)
    
    # Zlicz wystąpienia
    token_counts = Counter(all_tokens)
    
    # Filtruj rzadkie słowa
    keywords = {word: count for word, count in token_counts.items() 
               if count >= min_frequency}
    
    return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True))

def analyze_text_categories(texts, categories):
    """Analizuje teksty według kategorii (np. Shorts vs Long-form)."""
    results = {}
    
    for category in set(categories):
        category_texts = [text for text, cat in zip(texts, categories) if cat == category]
        keywords = extract_keywords_from_titles(category_texts)
        results[category] = keywords
    
    return results 