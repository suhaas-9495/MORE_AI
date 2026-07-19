import pytest
from fastapi.testclient import TestClient
import os
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["SECRET_KEY"] = "ci-test-secret-key-32-chars-minimum-xx"
os.environ["LANGFUSE_PUBLIC_KEY"] = "test"
os.environ["LANGFUSE_SECRET_KEY"] = "test"
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_REGION"] = "ap-south-1"
os.environ["AWS_S3_BUCKET"] = "test-bucket"

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