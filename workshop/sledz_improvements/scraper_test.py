#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🕷️ SCRAPER TEST - Test scrapowania Channel ID z YouTube
======================================================

Test kodu użytkownika do wyciągania Channel ID bez API
"""

import requests
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_channel_id(url):
    try:
        print(f"🔍 Sprawdzam: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        html = response.text

        # Szukaj ID kanału (YouTube handle: @nazwa)
        handle_match = re.search(r'"channelId":"(UC[\w-]{22})"', html)
        if handle_match:
            channel_id = handle_match.group(1)
            print(f"   ✅ Znaleziono przez handle: {channel_id}")
            return channel_id

        # Szukaj ID z klasycznych kanałów
        match = re.search(r"youtube\.com/channel/(UC[\w-]{22})", url)
        if match:
            channel_id = match.group(1)
            print(f"   ✅ Znaleziono przez URL: {channel_id}")
            return match.group(1)
        
        # Dodatkowe wzorce
        additional_patterns = [
            r'"browseEndpoint":{"browseId":"(UC[\w-]{22})"',
            r'"channelMetadataRenderer":{"title":"[^"]+","description":"[^"]*","rssUrl":"[^"]*","channelUrl":"[^"]*","ownerUrls":\["[^"]*"\],"avatar"[^}]+},"channelId":"(UC[\w-]{22})"',
            r'<meta property="og:url" content="https://www\.youtube\.com/channel/(UC[\w-]{22})"'
        ]
        
        for pattern in additional_patterns:
            match = re.search(pattern, html)
            if match:
                channel_id = match.group(1)
                print(f"   ✅ Znaleziono przez wzorzec dodatkowy: {channel_id}")
                return channel_id

        print(f"   ❌ Nie znaleziono Channel ID")
        return None

    except Exception as e:
        print(f"   💥 Błąd przy {url}: {e}")

    return None


def get_channel_ids_from_links(links):
    ids = {}
    for i, link in enumerate(links):
        print(f"\n📋 Test {i+1}/{len(links)}")
        
        # Pauza między requestami żeby nie przeciążać YouTube
        if i > 0:
            time.sleep(1)
            
        cid = extract_channel_id(link.strip())
        if cid:
            ids[link] = cid
        
    return ids


if __name__ == "__main__":
    print("🕷️ TEST SCRAPOWANIA CHANNEL ID")
    print("=" * 50)
    
    sample_links = [
        "https://www.youtube.com/@pudelektv",
        "https://www.youtube.com/@radiozet", 
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # link do filmu
    ]

    print(f"🎯 Testuję {len(sample_links)} linków...")
    
    start_time = time.time()
    results = get_channel_ids_from_links(sample_links)
    end_time = time.time()

    print(f"\n📊 WYNIKI:")
    print("=" * 30)
    
    for link, cid in results.items():
        print(f"✅ {link}")
        print(f"   → {cid}")
    
    failed = len(sample_links) - len(results)
    if failed > 0:
        print(f"\n❌ Nie udało się: {failed} linków")
    
    print(f"\n⏱️ Czas wykonania: {end_time - start_time:.1f}s")
    print(f"💰 Koszt quota API: 0 (scraping)")
    print(f"🌐 Ilość requestów HTTP: {len(sample_links)}") 