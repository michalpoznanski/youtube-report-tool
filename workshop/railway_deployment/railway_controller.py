#!/usr/bin/env python3
"""
RAILWAY CONTROLLER - STEROWANIE SERWEREM
========================================

Kontroluje Railway serwer przez API
"""

import requests
import json
import time
from datetime import datetime

class RailwayController:
    """Kontroler Railway serwera"""
    
    def __init__(self, railway_token=None):
        self.railway_token = railway_token
        self.base_url = "https://backboard.railway.app/graphql/v2"
        self.project_id = None  # Będzie pobrane automatycznie
        
        # Headers dla Railway API
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {railway_token}" if railway_token else None
        }
        
        print("🚂 Railway Controller uruchomiony")
    
    def get_project_info(self):
        """Pobiera informacje o projekcie"""
        query = """
        query {
            projects {
                id
                name
                description
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            response = requests.post(
                self.base_url,
                json={"query": query},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("data", {}).get("projects", [])
                
                # Znajdź projekt hookboost
                for project in projects:
                    if "hookboost" in project.get("name", "").lower():
                        self.project_id = project["id"]
                        return project
                
                print("⚠️ Nie znaleziono projektu hookboost")
                return None
            else:
                print(f"❌ Błąd API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Błąd pobierania projektu: {e}")
            return None
    
    def restart_service(self, service_name="hookboost"):
        """Restartuje serwis na Railway"""
        
        if not self.project_id:
            project = self.get_project_info()
            if not project:
                return False
        
        mutation = """
        mutation restartService($serviceId: String!) {
            serviceRestart(serviceId: $serviceId) {
                id
                name
                status
            }
        }
        """
        
        try:
            # Najpierw pobierz serwisy
            services_query = """
            query getServices($projectId: String!) {
                project(id: $projectId) {
                    services {
                        id
                        name
                        status
                    }
                }
            }
            """
            
            response = requests.post(
                self.base_url,
                json={
                    "query": services_query,
                    "variables": {"projectId": self.project_id}
                },
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("data", {}).get("project", {}).get("services", [])
                
                # Znajdź serwis hookboost
                service_id = None
                for service in services:
                    if service_name.lower() in service.get("name", "").lower():
                        service_id = service["id"]
                        break
                
                if not service_id:
                    print(f"❌ Nie znaleziono serwisu: {service_name}")
                    return False
                
                # Restart serwisu
                response = requests.post(
                    self.base_url,
                    json={
                        "query": mutation,
                        "variables": {"serviceId": service_id}
                    },
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Serwis {service_name} zrestartowany!")
                    return True
                else:
                    print(f"❌ Błąd restartu: {response.status_code}")
                    return False
            else:
                print(f"❌ Błąd pobierania serwisów: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Błąd restartu serwisu: {e}")
            return False
    
    def get_service_status(self, service_name="hookboost"):
        """Sprawdza status serwisu"""
        
        if not self.project_id:
            project = self.get_project_info()
            if not project:
                return None
        
        query = """
        query getServiceStatus($projectId: String!) {
            project(id: $projectId) {
                services {
                    id
                    name
                    status
                    createdAt
                    updatedAt
                }
            }
        }
        """
        
        try:
            response = requests.post(
                self.base_url,
                json={
                    "query": query,
                    "variables": {"projectId": self.project_id}
                },
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("data", {}).get("project", {}).get("services", [])
                
                for service in services:
                    if service_name.lower() in service.get("name", "").lower():
                        return service
                
                print(f"❌ Nie znaleziono serwisu: {service_name}")
                return None
            else:
                print(f"❌ Błąd API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Błąd sprawdzania statusu: {e}")
            return None
    
    def deploy_and_restart(self):
        """Deploy i restart serwisu"""
        print("🚀 Rozpoczynam deploy i restart...")
        
        # 1. Sprawdź status
        status = self.get_service_status()
        if status:
            print(f"📊 Status przed restartem: {status.get('status', 'UNKNOWN')}")
        
        # 2. Restart
        if self.restart_service():
            print("✅ Deploy i restart zakończone!")
            
            # 3. Sprawdź nowy status
            time.sleep(5)  # Poczekaj na restart
            new_status = self.get_service_status()
            if new_status:
                print(f"📊 Status po restarcie: {new_status.get('status', 'UNKNOWN')}")
            
            return True
        else:
            print("❌ Błąd deploy i restart")
            return False

# DEMO UŻYCIA
if __name__ == "__main__":
    # Railway token (jeśli masz)
    # 🛡️ BEZPIECZEŃSTWO: Token usunięty!
    RAILWAY_TOKEN = os.getenv("RAILWAY_TOKEN")
    if not RAILWAY_TOKEN:
        raise ValueError("❌ Brak RAILWAY_TOKEN w zmiennych środowiskowych!")
    
    controller = RailwayController(RAILWAY_TOKEN)
    
    print("\n🎯 DOSTĘPNE OPCJE:")
    print("1. controller.get_project_info() - info o projekcie")
    print("2. controller.get_service_status() - status serwisu")
    print("3. controller.restart_service() - restart serwisu")
    print("4. controller.deploy_and_restart() - deploy + restart")
    
    # Test z tokenem
    print("\n🧪 TEST Z TOKENEM:")
    project = controller.get_project_info()
    if project:
        print(f"✅ Projekt: {project.get('name', 'N/A')}")
        
        # Sprawdź status serwisu
        status = controller.get_service_status()
        if status:
            print(f"📊 Status serwisu: {status.get('status', 'UNKNOWN')}")
    else:
        print("❌ Problem z dostępem do projektu") 