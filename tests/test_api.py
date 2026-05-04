from __future__ import annotations

from tempfile import mkdtemp

from fastapi.testclient import TestClient

from devcd.host import create_app
from devcd.kernel.settings import DevCDSettings


def build_client(base_url: str = "http://127.0.0.1:8765") -> TestClient:
    settings = DevCDSettings(
        api_token="test-token",
        runtime_dir=mkdtemp(prefix="devcd-api-test-"),
        working_memory_ttl_seconds=315360000,
    )
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


def test_app_wires_ambient_context_service() -> None:
    settings = DevCDSettings(api_token="test-token", runtime_dir=mkdtemp(prefix="devcd-api-test-"))
    app = create_app(settings)

    assert hasattr(app.state, "ambient_context_service")


def test_context_work_state_api_returns_derived_state() -> None:
    client = build_client()
    headers = {"Authorization": "Bearer test-token"}
    client.post(
        "/event",
        headers=headers,
        json={
            "source": "task",
            "type": "goal_update",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"current_goal": "Implement ambient context kernel"},
        },
    )

    response = client.get("/context/work-state", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["active_intent"]["summary"] == "Implement ambient context kernel"
    assert body["policy_summary"]["operation"] == "export"


def test_context_brief_api_returns_policy_filtered_brief() -> None:
    client = build_client()
    headers = {"Authorization": "Bearer test-token"}
    client.post(
        "/event",
        headers=headers,
        json={
            "source": "task",
            "type": "goal_update",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"current_goal": "Implement ambient context kernel"},
        },
    )

    response = client.post(
        "/context/brief",
        headers=headers,
        json={"kind": "http", "name": "test-agent", "detail_level": "standard"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["active_intent"]["summary"] == "Implement ambient context kernel"
    assert body["policy_decision"]["operation"] == "export"


def test_context_suggestion_dismiss_api_suppresses_suggestion() -> None:
    client = build_client()
    headers = {"Authorization": "Bearer test-token"}
    client.post(
        "/event",
        headers=headers,
        json={
            "source": "task",
            "type": "test_failure",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"reason": "context brief omits open loop evidence"},
        },
    )
    work_state = client.get("/context/work-state", headers=headers).json()
    suggestion_id = work_state["suggestions"][0]["id"]

    response = client.post(
        f"/context/suggestions/{suggestion_id}/dismiss",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"
    assert client.get("/context/work-state", headers=headers).json()["suggestions"] == []


def test_context_memory_api_lists_corrects_and_deletes_items() -> None:
    client = build_client()
    headers = {"Authorization": "Bearer test-token"}
    client.post(
        "/event",
        headers=headers,
        json={
            "source": "task",
            "type": "goal_update",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"current_goal": "Old goal"},
        },
    )
    items = client.get("/context/memory?scope=working", headers=headers).json()
    item_id = items[0]["id"]

    correction = client.patch(
        f"/context/memory/{item_id}",
        headers=headers,
        json={"summary": "Corrected goal", "reason": "developer corrected retained context"},
    )
    deleted = client.delete(f"/context/memory/{item_id}", headers=headers)

    assert correction.status_code == 200
    assert correction.json()["summary"] == "goal_update: Corrected goal"
    assert deleted.status_code == 204
    assert client.get("/context/memory?scope=working", headers=headers).json() == []
