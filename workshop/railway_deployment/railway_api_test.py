#!/usr/bin/env python3
"""
RAILWAY API TEST - SPRAWDZANIE DOSTĘPU
=====================================

Testuje różne Railway API endpointy
"""

import requests
import json

# Token z Railway
RAILWAY_TOKEN = "01cb5053-0fac-4ffe-9618-c7af6466902d"

def test_railway_api():
    """Testuje różne Railway API endpointy"""
    
    print("🧪 TEST RAILWAY API")
    print("=" * 40)
    
    # Różne endpointy do przetestowania
    endpoints = [
        {
            "name": "GraphQL v2",
            "url": "https://backboard.railway.app/graphql/v2",
            "headers": {
                "Authorization": f"Bearer {RAILWAY_TOKEN}",
                "Content-Type": "application/json"
            },
            "data": {
                "query": "{ projects { id name } }"
            }
        },
        {
            "name": "REST API v2",
            "url": "https://api.railway.app/v2/projects",
            "headers": {
                "Authorization": f"Bearer {RAILWAY_TOKEN}"
            },
            "data": None
        },
        {
            "name": "REST API v1",
            "url": "https://api.railway.app/v1/projects",
            "headers": {
                "Authorization": f"Bearer {RAILWAY_TOKEN}"
            },
            "data": None
        },
        {
            "name": "Dashboard API",
            "url": "https://backboard.railway.app/api/projects",
            "headers": {
                "Authorization": f"Bearer {RAILWAY_TOKEN}"
            },
            "data": None
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testuję: {endpoint['name']}")
        print(f"📡 URL: {endpoint['url']}")
        
        try:
            if endpoint['data']:
                response = requests.post(
                    endpoint['url'],
                    json=endpoint['data'],
                    headers=endpoint['headers'],
                    timeout=10
                )
            else:
                response = requests.get(
                    endpoint['url'],
                    headers=endpoint['headers'],
                    timeout=10
                )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUKCES!")
                try:
                    data = response.json()
                    print(f"📄 Odpowiedź: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"📄 Odpowiedź: {response.text[:200]}...")
            else:
                print(f"❌ BŁĄD: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ BŁĄD: {e}")

def test_token_validity():
    """Sprawdza czy token jest poprawny"""
    
    print("\n🔑 TEST WALIDACJI TOKENU")
    print("=" * 40)
    
    # Sprawdź format tokenu
    if len(RAILWAY_TOKEN) == 36 and RAILWAY_TOKEN.count('-') == 4:
        print("✅ Format tokenu wygląda poprawnie (UUID)")
    else:
        print("❌ Format tokenu nie wygląda jak UUID")
    
    # Sprawdź czy token nie jest ukryty
    if RAILWAY_TOKEN.startswith('****'):
        print("❌ Token wygląda na ukryty - potrzebujesz pełnego tokenu")
    else:
        print("✅ Token nie jest ukryty")

if __name__ == "__main__":
    test_token_validity()
    test_railway_api() 