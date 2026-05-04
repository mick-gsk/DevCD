from __future__ import annotations

from tempfile import mkdtemp

from fastapi.testclient import TestClient

from devcd.host import create_app
from devcd.kernel.settings import DevCDSettings


def build_client(base_url: str = "http://127.0.0.1:8765") -> TestClient:
    settings = DevCDSettings(api_token="test-token", runtime_dir=mkdtemp(prefix="devcd-api-test-"))
    return TestClient(create_app(settings), base_url=base_url)


def test_event_api_updates_state() -> None:
    client = build_client()

    response = client.post(
        "/event",
        headers={"Authorization": "Bearer test-token"},
        json={
            "source": "ide",
            "type": "goal_update",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"current_goal": "Bootstrap DevCD", "subtask": "State API"},
        },
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "allow"
    assert response.json()["operation"] == "observe"

    state = client.get("/state", headers={"Authorization": "Bearer test-token"}).json()
    assert state["current_goal"] == "Bootstrap DevCD"
    assert state["subtask"] == "State API"
    assert state["source_active_map"] == {"ide": True}


def test_memory_api_returns_working_memory() -> None:
    client = build_client()
    client.post(
        "/event",
        headers={"Authorization": "Bearer test-token"},
        json={
            "source": "git",
            "type": "branch_change",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"branch": "feature/devcd-mvp"},
        },
    )

    response = client.get("/memory/working", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()[0]["content"]["type"] == "branch_change"


def test_memory_api_rejects_invalid_scope() -> None:
    client = build_client()

    response = client.get("/memory/invalid", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 422


def test_api_rejects_missing_and_invalid_token() -> None:
    client = build_client()

    missing_token = client.get("/state")
    invalid_token = client.get("/state", headers={"Authorization": "Bearer wrong-token"})

    assert missing_token.status_code == 401
    assert missing_token.json()["operation"] == "auth"
    assert invalid_token.status_code == 401
    assert invalid_token.json()["operation"] == "auth"


def test_api_rejects_non_loopback_access() -> None:
    client = build_client(base_url="http://example.com")

    response = client.get("/state", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 401
    assert response.json()["operation"] == "auth"
    assert "non-loopback" in response.json()["reason"]
