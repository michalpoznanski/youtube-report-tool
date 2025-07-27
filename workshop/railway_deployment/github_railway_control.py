#!/usr/bin/env python3
"""
GITHUB RAILWAY CONTROL
======================

Kontrola Railway przez GitHub Actions
"""

import requests
import json
import time
from datetime import datetime

class GitHubRailwayControl:
    def __init__(self, github_token):
        self.github_token = github_token
        self.repo = "michalpoznanski/hookboost"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def trigger_railway_restart(self):
        """Triggeruje restart Railway przez GitHub Actions"""
        
        # 1. Sprawdź czy workflow istnieje
        workflow_url = f"https://api.github.com/repos/{self.repo}/actions/workflows"
        response = requests.get(workflow_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Błąd sprawdzania workflow: {response.status_code}")
            return False
        
        workflows = response.json().get("workflows", [])
        railway_workflow = None
        
        for workflow in workflows:
            if "railway" in workflow.get("name", "").lower():
                railway_workflow = workflow
                break
        
        if not railway_workflow:
            print("❌ Nie znaleziono Railway workflow")
            return False
        
        # 2. Trigger workflow z akcją restart
        workflow_id = railway_workflow["id"]
        trigger_url = f"https://api.github.com/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches"
        
        data = {
            "ref": "main",
            "inputs": {
                "action": "restart"
            }
        }
        
        response = requests.post(trigger_url, headers=self.headers, json=data)
        
        if response.status_code == 204:
            print("✅ Railway restart wytriggerowany przez GitHub Actions!")
            return True
        else:
            print(f"❌ Błąd triggerowania: {response.status_code}")
            return False
    
    def trigger_railway_deploy(self):
        """Triggeruje deploy Railway przez GitHub Actions"""
        
        # 1. Sprawdź czy workflow istnieje
        workflow_url = f"https://api.github.com/repos/{self.repo}/actions/workflows"
        response = requests.get(workflow_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Błąd sprawdzania workflow: {response.status_code}")
            return False
        
        workflows = response.json().get("workflows", [])
        railway_workflow = None
        
        for workflow in workflows:
            if "railway" in workflow.get("name", "").lower():
                railway_workflow = workflow
                break
        
        if not railway_workflow:
            print("❌ Nie znaleziono Railway workflow")
            return False
        
        # 2. Trigger workflow z akcją deploy
        workflow_id = railway_workflow["id"]
        trigger_url = f"https://api.github.com/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches"
        
        data = {
            "ref": "main",
            "inputs": {
                "action": "deploy"
            }
        }
        
        response = requests.post(trigger_url, headers=self.headers, json=data)
        
        if response.status_code == 204:
            print("✅ Railway deploy wytriggerowany przez GitHub Actions!")
            return True
        else:
            print(f"❌ Błąd triggerowania: {response.status_code}")
            return False
    
    def get_railway_status(self):
        """Sprawdza status Railway przez GitHub Actions"""
        
        # 1. Sprawdź ostatnie workflow runs
        runs_url = f"https://api.github.com/repos/{self.repo}/actions/runs"
        response = requests.get(runs_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Błąd sprawdzania runs: {response.status_code}")
            return None
        
        runs = response.json().get("workflow_runs", [])
        
        # Znajdź ostatni Railway run
        railway_runs = [run for run in runs if "railway" in run.get("name", "").lower()]
        
        if not railway_runs:
            print("❌ Nie znaleziono Railway workflow runs")
            return None
        
        latest_run = railway_runs[0]
        
        return {
            "status": latest_run.get("status"),
            "conclusion": latest_run.get("conclusion"),
            "created_at": latest_run.get("created_at"),
            "updated_at": latest_run.get("updated_at"),
            "html_url": latest_run.get("html_url")
        }

def test_github_railway_control():
    """Testuje GitHub Railway Control"""
    
    GITHUB_TOKEN = "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"
    
    controller = GitHubRailwayControl(GITHUB_TOKEN)
    
    print("🧪 TEST GITHUB RAILWAY CONTROL")
    print("=" * 40)
    
    # 1. Sprawdź status
    print("\n📊 Sprawdzam status Railway...")
    status = controller.get_railway_status()
    if status:
        print(f"✅ Status: {status['status']}")
        print(f"📋 Conclusion: {status['conclusion']}")
        print(f"🕐 Ostatnia aktualizacja: {status['updated_at']}")
        print(f"🔗 Link: {status['html_url']}")
    
    # 2. Test restart
    print("\n🚂 Testuję restart Railway...")
    restart_success = controller.trigger_railway_restart()
    
    if restart_success:
        print("✅ Restart wytriggerowany!")
        
        # Poczekaj i sprawdź status
        print("⏳ Czekam 10 sekund...")
        time.sleep(10)
        
        new_status = controller.get_railway_status()
        if new_status:
            print(f"📊 Nowy status: {new_status['status']}")

if __name__ == "__main__":
    test_github_railway_control() 