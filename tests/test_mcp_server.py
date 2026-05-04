from __future__ import annotations

import json
from datetime import UTC, datetime

from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.mcp_server.service import READ_ONLY_RESOURCE_URIS, ReadOnlyMCPServer
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def test_mcp_server_lists_only_read_only_resources_and_no_tools(tmp_path) -> None:
    server, _state_engine = build_mcp_server(tmp_path)

    initialized = server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    resources = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})
    tools = server.handle_message({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})

    assert initialized is not None
    assert initialized["result"]["serverInfo"]["name"] == "devcd"
    assert initialized["result"]["capabilities"] == {"resources": {}}
    assert resources is not None
    assert [resource["uri"] for resource in resources["result"]["resources"]] == list(
        READ_ONLY_RESOURCE_URIS
    )
    assert tools == {"jsonrpc": "2.0", "id": 3, "result": {"tools": []}}


def test_mcp_server_reads_context_brief_without_external_client(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Implement read-only MCP context server"},
        )
    )

    response = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "devcd://context/brief"},
        }
    )

    assert response is not None
    body = json.loads(response["result"]["contents"][0]["text"])
    assert body["surface"]["kind"] == "mcp"
    assert body["active_intent"]["summary"] == "Implement read-only MCP context server"
    assert body["policy_decision"]["operation"] == "export"


def test_mcp_server_withholds_sensitive_context_without_payload(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"title": "Private credentials note"},
            sensitivity="sensitive",
        )
    )

    response = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uri": "devcd://context/withheld-context"},
        }
    )

    assert response is not None
    body_text = response["result"]["contents"][0]["text"]
    body = json.loads(body_text)
    assert "Private credentials note" not in body_text
    assert body["withheld_context"][0]["category"] == "sensitivity"
    assert "sensitive events" in body["withheld_context"][0]["policy_reason"]


def test_mcp_server_reads_recent_events_and_policy_decisions(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
            payload={"branch": "main"},
        )
    )

    recent_events = read_resource(server, "devcd://context/recent-events")
    policy_decisions = read_resource(server, "devcd://context/policy-decisions")

    assert recent_events["recent_events"][0]["type"] == "branch_change"
    assert recent_events["recent_events"][0]["payload"] == {"branch": "main"}
    assert policy_decisions["policy_decisions"][0]["kind"] == "allow"
    assert policy_decisions["policy_decisions"][0]["operation"] == "store"


def test_mcp_server_rejects_unknown_resource(tmp_path) -> None:
    server, _state_engine = build_mcp_server(tmp_path)

    response = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {"uri": "devcd://context/missing"},
        }
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert "unknown resource" in response["error"]["message"]


def read_resource(server: ReadOnlyMCPServer, uri: str) -> dict[str, object]:
    response = server.handle_message(
        {"jsonrpc": "2.0", "id": 6, "method": "resources/read", "params": {"uri": uri}}
    )
    assert response is not None
    return json.loads(response["result"]["contents"][0]["text"])


def build_mcp_server(tmp_path) -> tuple[ReadOnlyMCPServer, StateEngine]:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    ambient_context_service = AmbientContextService(state_engine, memory_store, policy_engine)
    return (
        ReadOnlyMCPServer(
            ambient_context_service=ambient_context_service,
            state_engine=state_engine,
            event_ledger=event_ledger,
            policy_engine=policy_engine,
        ),
        state_engine,
    )
