import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_status_endpoint():
    """Test status endpoint"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "scheduler_running" in data
    assert "channels_count" in data
    assert "categories" in data
    assert "quota_usage" in data


def test_channels_endpoint():
    """Test channels endpoint"""
    response = client.get("/api/v1/channels")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_add_channel_invalid_url():
    """Test adding channel with invalid URL"""
    response = client.post("/api/v1/channels", json={
        "url": "invalid_url",
        "category": "test"
    })
    assert response.status_code == 400


def test_generate_report_no_channels():
    """Test generating report when no channels exist"""
    response = client.post("/api/v1/reports/generate", json={
        "category": None,
        "days_back": 3
    })
    assert response.status_code == 404


def test_reports_list():
    """Test reports list endpoint"""
    response = client.get("/api/v1/reports/list")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert isinstance(data["reports"], list)


def test_scheduler_control():
    """Test scheduler control endpoints"""
    # Start scheduler
    response = client.post("/api/v1/scheduler/start")
    assert response.status_code == 200
    
    # Stop scheduler
    response = client.post("/api/v1/scheduler/stop")
    assert response.status_code == 200 