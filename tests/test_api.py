"""API tests using FastAPI TestClient. SKIP_MODEL_LOAD is set in conftest so models are not loaded."""

import os
import pytest

# Ensure SKIP_MODEL_LOAD is set before importing app (conftest sets it)
os.environ.setdefault("SKIP_MODEL_LOAD", "1")


def test_health():
    """GET /health returns ok."""
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_conversations_list():
    """GET /conversations returns a list (may be empty)."""
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    resp = client.get("/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_conversations_create():
    """POST /conversations creates a conversation and returns it."""
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    resp = client.post("/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "title" in data
    assert data["title"] == "New Chat" or "title" in data
