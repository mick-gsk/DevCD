from __future__ import annotations

from fastapi.testclient import TestClient

from devcd.host import create_app


def test_event_api_updates_state() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/event",
        json={
            "source": "ide",
            "type": "goal_update",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"current_goal": "Bootstrap DevCD", "subtask": "State API"},
        },
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "allow"

    state = client.get("/state").json()
    assert state["current_goal"] == "Bootstrap DevCD"
    assert state["subtask"] == "State API"


def test_memory_api_returns_working_memory() -> None:
    client = TestClient(create_app())
    client.post(
        "/event",
        json={
            "source": "git",
            "type": "branch_change",
            "timestamp": "2026-05-04T12:00:00Z",
            "payload": {"branch": "feature/devcd-mvp"},
        },
    )

    response = client.get("/memory/working")

    assert response.status_code == 200
    assert response.json()[0]["content"]["type"] == "branch_change"
