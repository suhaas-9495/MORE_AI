import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    # register
    r = client.post("/auth/register", json={
        "username": "ci_test_user",
        "password": "testpass123"
    })
    assert r.status_code in [201, 400]  # 400 if already exists

    # login
    r = client.post("/auth/login", json={
        "username": "ci_test_user",
        "password": "testpass123"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_agent_requires_auth():
    r = client.post("/agent/run", json={
        "task": "test task",
        "agent_type": "planner"
    })
    assert r.status_code == 403


def test_registry_requires_auth():
    r = client.get("/registry/tools")
    assert r.status_code == 403