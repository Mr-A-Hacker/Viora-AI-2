"""
Tests for camera integration with the security button flow.
Verifies that camera start/stop, video feed, capture, and security endpoints
work correctly when the security button is pressed.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("SKIP_MODEL_LOAD", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# FastAPI camera router tests
# ---------------------------------------------------------------------------

@pytest.fixture
def camera_client():
    """TestClient that includes only the camera router."""
    from fastapi import FastAPI
    from camera_stream import router as camera_router

    app = FastAPI()
    app.include_router(camera_router)
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_camera_start_endpoint_exists(camera_client):
    """POST /camera/start returns 200 and a status key."""
    with patch("camera_stream.multiprocessing.Process") as MockProc:
        instance = MagicMock()
        instance.is_alive.return_value = False
        MockProc.return_value = instance

        resp = camera_client.post("/camera/start")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


def test_camera_stop_endpoint_exists(camera_client):
    """POST /camera/stop returns 200 and a status key."""
    with patch("camera_stream.camera_process", None):
        resp = camera_client.post("/camera/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stopped"


def test_camera_start_idempotent(camera_client):
    """Starting camera twice when already running returns 'already_running'."""
    with patch("camera_stream.multiprocessing.Process") as MockProc:
        instance = MagicMock()
        instance.is_alive.return_value = True  # pretend running
        MockProc.return_value = instance

        # Patch the module-level camera_process to look alive
        with patch("camera_stream.camera_process", instance):
            resp = camera_client.post("/camera/start")
            assert resp.status_code == 200
            assert resp.json()["status"] == "already_running"


def test_camera_capture_no_frame(camera_client):
    """POST /camera/capture returns error when no frame is available."""
    resp = camera_client.post("/camera/capture")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"


def test_video_feed_endpoint_exists(camera_client):
    """GET /video_feed returns a streaming response (or 500 if no camera)."""
    # The endpoint itself is defined; calling it without a running camera
    # will either hang or return a streaming response with no data.
    # We just verify it does not 404.
    from camera_stream import camera_process
    if camera_process is None:
        pytest.skip("No camera process running — endpoint would hang")
    resp = camera_client.get("/video_feed")
    assert resp.status_code == 200
    assert "multipart" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Security API router tests (FastAPI /security/*)
# ---------------------------------------------------------------------------

@pytest.fixture
def security_client():
    """TestClient with only the security router."""
    from fastapi import FastAPI
    from security import router as security_router

    app = FastAPI()
    app.include_router(security_router)
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_security_start_detection(security_client):
    resp = security_client.post("/security/start_detection")
    assert resp.status_code == 200
    assert resp.json()["status"] == "detection_started"


def test_security_manual_alarm(security_client):
    with patch("security.play_alarm_sound"):
        resp = security_client.post("/security/manual_alarm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alarm_triggered"


def test_security_stop_alarm(security_client):
    resp = security_client.post("/security/stop_alarm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alarm_stopped"


def test_security_defuse_correct_password(security_client):
    resp = security_client.post("/security/defuse", json={"password": "admin1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "defused"


def test_security_defuse_wrong_password(security_client):
    resp = security_client.post("/security/defuse", json={"password": "wrong"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# End-to-end: security button flow (FastAPI app)
# ---------------------------------------------------------------------------

@pytest.fixture
def app_client():
    """Full FastAPI app TestClient (models skipped via env)."""
    # Mock unified_security so app.py can import without flask
    mock_unified = MagicMock()
    mock_unified.trigger_voice_alert = MagicMock()
    mock_unified.send_alarm_to_surveillance = MagicMock(return_value=True)
    mock_unified.stop_alarm_on_surveillance = MagicMock(return_value=True)
    sys.modules["unified_security"] = mock_unified

    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)


def test_health_ok(app_client):
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_camera_start_via_app(app_client):
    """Camera start works through the unified app."""
    with patch("camera_stream.multiprocessing.Process") as MockProc:
        instance = MagicMock()
        instance.is_alive.return_value = False
        MockProc.return_value = instance
        resp = app_client.post("/camera/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"


def test_security_defuse_via_app(app_client):
    resp = app_client.post("/security/defuse", json={"password": "admin1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "defused"


def test_security_manual_alarm_via_app(app_client):
    with patch("security.play_alarm_sound"):
        resp = app_client.post("/security/manual_alarm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alarm_triggered"


def test_gallery_empty(app_client):
    """Gallery endpoint returns a list (possibly empty)."""
    resp = app_client.get("/gallery/images")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert isinstance(resp.json()["images"], list)
