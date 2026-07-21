from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_health_check_get():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check_head():
    response = client.head("/health")
    assert response.status_code == 200

def test_dashboard_loads():
    response = client.get("/")
    assert response.status_code == 200
    content = response.text
    # Verify Jinja2 template rendered some expected HTML elements
    assert "Sales Analytics Dashboard" in content
    assert "Total Revenue" in content
    assert "Total Profit" in content
    assert "Avg Margin" in content
    assert "Avg Ship Days" in content
    
    # Ensure plotly object is passed
    assert "Plotly.newPlot" in content
