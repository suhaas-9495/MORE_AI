import pytest
from fastapi.testclient import TestClient
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-32-chars-minimum-xx")
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "test")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "test")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_S3_BUCKET", "test-bucket")

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register():
    r = client.post("/auth/register", json={
        "username": "ci_user",
        "password": "testpass123"
    })
    assert r.status_code in [201, 400]


def test_login():
    client.post("/auth/register", json={
        "username": "ci_user2",
        "password": "testpass123"
    })
    r = client.post("/auth/login", json={
        "username": "ci_user2",
        "password": "testpass123"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_agent_requires_auth():
    r = client.post("/agent/run", json={
        "task": "test",
        "agent_type": "planner"
    })
    assert r.status_code in [401, 403]