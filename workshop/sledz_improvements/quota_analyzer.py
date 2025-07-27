#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 QUOTA ANALYZER - Analiza kosztów !śledź
==========================================

Cel: Zrozumieć dokładnie ile kosztuje każda operacja w !śledź
"""

class QuotaAnalyzer:
    """Analizuje koszty quota dla różnych operacji !śledź"""
    
    def analyze_sledz_costs(self):
        """Analizuje koszty różnych scenariuszy !śledź"""
        
        print("🔍 ANALIZA KOSZTÓW !ŚLEDŹ")
        print("=" * 50)
        
        scenarios = [
            {
                "name": "Gotowy Channel ID",
                "example": "UCShUU9VW-unGNHC-3XMUSmQ",
                "description": "Link z gotowym Channel ID",
                "api_calls": [],
                "quota_cost": 0,
                "reason": "Nie wymaga zapytań do API - ID już znane"
            },
            {
                "name": "@handle",
                "example": "@swiatgwiazd",
                "description": "Link z @handle",
                "api_calls": ["channels.list (forUsername)"],
                "quota_cost": 1,
                "reason": "1 zapytanie do channels API aby znaleźć Channel ID"
            },
            {
                "name": "Link do filmu",
                "example": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "Link do konkretnego filmu",
                "api_calls": ["videos.list", "channels.list"],
                "quota_cost": 2,
                "reason": "1 zapytanie o film + 1 zapytanie o kanał właściciela"
            },
            {
                "name": "/c/nazwa",
                "example": "https://youtube.com/c/swiatgwiazd",
                "description": "Link z niestandardową nazwą",
                "api_calls": ["search.list"],
                "quota_cost": 100,
                "reason": "Kosztowne search query - należy unikać!"
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📋 **{scenario['name']}**")
            print(f"   Przykład: {scenario['example']}")
            print(f"   Opis: {scenario['description']}")
            print(f"   API Calls: {', '.join(scenario['api_calls']) if scenario['api_calls'] else 'Brak'}")
            print(f"   💰 Koszt: {scenario['quota_cost']} quota")
            print(f"   📝 Powód: {scenario['reason']}")
        
        print(f"\n🎯 **PODSUMOWANIE:**")
        print(f"   • Najtańsze: Gotowe Channel ID (0 quota)")
        print(f"   • Akceptowalne: @handle (1 quota)")
        print(f"   • Drogie: Linki filmów (2 quota)")
        print(f"   • UNIKAĆ: /c/nazwa (100 quota!)")
        
        return scenarios
    
    def analyze_batch_costs(self):
        """Analizuje koszty dodawania wielu kanałów jednocześnie"""
        
        print("\n" + "=" * 50)
        print("🔢 ANALIZA KOSZTÓW WSADOWYCH")
        print("=" * 50)
        
        examples = [
            {
                "links": 5,
                "channel_ids": 3,
                "handles": 2,
                "videos": 0,
                "total_cost": 3 * 0 + 2 * 1 + 0 * 2,
                "breakdown": "3×0 + 2×1 + 0×2 = 2 quota"
            },
            {
                "links": 10,
                "channel_ids": 5,
                "handles": 3,
                "videos": 2,
                "total_cost": 5 * 0 + 3 * 1 + 2 * 2,
                "breakdown": "5×0 + 3×1 + 2×2 = 7 quota"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n📊 **Przykład {i}:**")
            print(f"   Łącznie linków: {example['links']}")
            print(f"   - Channel ID: {example['channel_ids']} (×0 quota)")
            print(f"   - @handles: {example['handles']} (×1 quota)")
            print(f"   - Filmy: {example['videos']} (×2 quota)")
            print(f"   💰 Łączny koszt: {example['total_cost']} quota")
            print(f"   📝 Kalkulacja: {example['breakdown']}")

if __name__ == "__main__":
    analyzer = QuotaAnalyzer()
    analyzer.analyze_sledz_costs()
    analyzer.analyze_batch_costs()
    
    print("\n" + "=" * 50)
    print("💡 **WNIOSKI DLA INTERFEJSU:**")
    print("   1. Pokaż koszt quota przed wykonaniem")
    print("   2. Ostrzeż przed kosztownymi operacjami")
    print("   3. Wyświetl tylko liczbę kanałów (nie nazwy)")
    print("   4. Grupuj wyniki według typu operacji") 