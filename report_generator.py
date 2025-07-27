#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 REPORT GENERATOR - ULTRA LEAN
===============================

Prosty generator 17-kolumnowych CSV raportów:
- Tylko surowe metadane YouTube
- 3-dniowe snapshoty
- Auto-commit do GitHub
- Bez quota managera i analizy

AUTOR: Hook Boost V3 - Fresh Ultra Lean
WERSJA: 3.0.0 (2025-01-27)
"""

import os
import csv
import requests
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ReportGenerator:
    """Ultra prosty generator raportów CSV"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.max_videos = 20  # Max filmów na kanał
        
        print("📊 ReportGenerator V3 initialized")
    
    def _get_channel_uploads(self, channel_id: str) -> str:
        """Pobiera uploads playlist ID"""
        try:
            url = f"{self.base_url}/channels"
            params = {
                'part': 'contentDetails',
                'id': channel_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            return None
            
        except Exception as e:
            print(f"❌ Błąd uploads dla {channel_id}: {e}")
            return None
    
    def _get_videos_from_playlist(self, playlist_id: str) -> List[str]:
        """Pobiera video IDs z playlisty"""
        try:
            url = f"{self.base_url}/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': self.max_videos,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return [item['snippet']['resourceId']['videoId'] 
                    for item in data.get('items', [])]
            
        except Exception as e:
            print(f"❌ Błąd videos z {playlist_id}: {e}")
            return []
    
    def _get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Pobiera szczegóły filmów"""
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,statistics,contentDetails,status,topicDetails',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            videos = []
            for video in data.get('items', []):
                video_data = self._extract_17_columns(video)
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            print(f"❌ Błąd szczegółów filmów: {e}")
            return []
    
    def _extract_17_columns(self, video: Dict) -> Dict[str, Any]:
        """Ekstraktuje dane do 17 kolumn (ULTRA-SUROWY)"""
        snippet = video.get('snippet', {})
        stats = video.get('statistics', {})
        content = video.get('contentDetails', {})
        
        return {
            'Channel_Name': snippet.get('channelTitle', 'Unknown'),
            'Date_of_Publishing': snippet.get('publishedAt', ''),
            'Hour_GMT2': self._convert_to_gmt2(snippet.get('publishedAt', '')),
            'Title': snippet.get('title', ''),
            'Description': snippet.get('description', '')[:500],  # Limit 500 chars
            'Tags': ','.join(snippet.get('tags', [])),
            'Video_Type': self._get_video_type(content),
            'View_Count': int(stats.get('viewCount', 0)),
            'Like_Count': int(stats.get('likeCount', 0)),
            'Comment_Count': int(stats.get('commentCount', 0)),
            'Favorite_Count': int(stats.get('favoriteCount', 0)),
            'Definition': content.get('definition', 'unknown'),
            'Has_Captions': content.get('caption', 'false'),
            'Licensed_Content': str(content.get('licensedContent', False)),
            'Topic_Categories': ','.join(video.get('topicDetails', {}).get('topicCategories', [])),
            'Names_Extracted': '',  # Puste - analiza offline
            'Video_ID': video.get('id', '')
        }
    
    def _convert_to_gmt2(self, published_at: str) -> str:
        """Konwertuje na GMT+2"""
        try:
            if not published_at:
                return ''
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            gmt2_dt = dt + timedelta(hours=2)
            return gmt2_dt.strftime('%H:%M')
        except:
            return ''
    
    def _get_video_type(self, content: Dict) -> str:
        """Określa typ filmu"""
        duration = content.get('duration', '')
        # Prosta detekcja shorts (<=60s)
        if 'PT' in duration and 'M' not in duration:
            try:
                seconds = int(duration.replace('PT', '').replace('S', ''))
                return 'short' if seconds <= 60 else 'regular'
            except:
                pass
        return 'regular'
    
    def _save_csv(self, room: str, videos: List[Dict]) -> str:
        """Zapisuje CSV z 17 kolumnami"""
        try:
            # Katalog raw_data
            os.makedirs("raw_data", exist_ok=True)
            
            # Nazwa pliku
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"raw_raport_{timestamp}_{room}.csv"
            filepath = os.path.join("raw_data", filename)
            
            # 17 kolumn ULTRA-SUROWEGO CSV
            fieldnames = [
                'Channel_Name', 'Date_of_Publishing', 'Hour_GMT2', 'Title',
                'Description', 'Tags', 'Video_Type', 'View_Count', 'Like_Count',
                'Comment_Count', 'Favorite_Count', 'Definition', 'Has_Captions',
                'Licensed_Content', 'Topic_Categories', 'Names_Extracted', 'Video_ID'
            ]
            
            # Zapisz CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(videos)
            
            print(f"💾 CSV saved: {filepath} ({len(videos)} videos)")
            
            # Auto-commit
            self._auto_commit(filepath)
            
            return filename
            
        except Exception as e:
            print(f"❌ Błąd zapisu CSV: {e}")
            return ""
    
    def _auto_commit(self, filepath: str):
        """Auto-commit do GitHub"""
        try:
            print("📤 Auto-commit do GitHub...")
            
            # Git operations
            subprocess.run(['git', 'add', filepath], check=True, capture_output=True)
            
            commit_msg = f"Auto-report: {os.path.basename(filepath)}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
            
            subprocess.run(['git', 'push'], check=True, capture_output=True)
            
            print("✅ Auto-commit successful")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git operation failed: {e}")
        except Exception as e:
            print(f"❌ Auto-commit error: {e}")
    
    def generate_report(self, room: str, channels: List[str]) -> Dict[str, Any]:
        """Główna funkcja generowania raportu"""
        try:
            all_videos = []
            processed_channels = 0
            
            for channel in channels:
                print(f"📺 Processing: {channel}")
                
                # Skip handles (wymagają resolving)
                if channel.startswith('@'):
                    print(f"⚠️ Skipping handle {channel} - requires API resolution")
                    continue
                
                # Pobierz uploads playlist
                uploads = self._get_channel_uploads(channel)
                if not uploads:
                    continue
                
                # Pobierz video IDs
                video_ids = self._get_videos_from_playlist(uploads)
                if not video_ids:
                    continue
                
                # Pobierz szczegóły
                videos = self._get_video_details(video_ids)
                all_videos.extend(videos)
                processed_channels += 1
                
                print(f"✅ {channel}: {len(videos)} videos")
            
            if not all_videos:
                return {
                    'success': False,
                    'error': 'Nie udało się zebrać żadnych filmów'
                }
            
            # Zapisz CSV
            filename = self._save_csv(room, all_videos)
            
            return {
                'success': True,
                'channels': processed_channels,
                'videos': len(all_videos),
                'filename': filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Błąd generowania: {str(e)}'
            } 