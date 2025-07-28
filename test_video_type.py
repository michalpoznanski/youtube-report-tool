#!/usr/bin/env python3
"""
Test logiki Video_Type (shorts vs long)
"""

from app.storage.csv_generator import CSVGenerator

def test_video_type_logic():
    """Testuje logikę określania typu filmu"""
    csv_gen = CSVGenerator()
    
    # Test cases
    test_cases = [
        # (duration, video_id, video_url, expected_type)
        ("PT30S", "abc123", "https://www.youtube.com/shorts/abc123", "shorts"),  # 30s + shorts URL
        ("PT30S", "abc123", "https://www.youtube.com/watch?v=abc123", "shorts"),  # 30s + regular URL (potencjalny shorts)
        ("PT2M30S", "abc123", "https://www.youtube.com/shorts/abc123", "long"),   # 2.5min + shorts URL
        ("PT2M30S", "abc123", "https://www.youtube.com/watch?v=abc123", "long"),  # 2.5min + regular URL
        ("PT1M", "abc123", "https://www.youtube.com/watch?v=abc123", "shorts"),   # 1min + regular URL (potencjalny shorts)
        ("PT1M1S", "abc123", "https://www.youtube.com/watch?v=abc123", "long"),   # 1min1s + regular URL
        ("", "abc123", "https://www.youtube.com/watch?v=abc123", "unknown"),      # Brak duration
    ]
    
    print("🧪 Test logiki Video_Type:")
    print("=" * 50)
    
    for i, (duration, video_id, video_url, expected) in enumerate(test_cases, 1):
        result = csv_gen._determine_video_type(duration, video_id, video_url)
        status = "✅" if result == expected else "❌"
        print(f"{status} Test {i}: {duration} + {video_url} -> {result} (expected: {expected})")
    
    print("\n📊 Podsumowanie:")
    print("- Duration < 60s + shorts URL = SHORTS")
    print("- Duration < 60s + regular URL = SHORTS (potencjalny)")
    print("- Duration >= 60s = LONG")
    print("- Brak duration = UNKNOWN")

if __name__ == "__main__":
    test_video_type_logic() 