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


def test_mcp_server_agent_handoff_packet_contains_goal_and_contract(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"current_goal": "Add agent handoff MCP resource"},
        )
    )

    body = read_resource(server, "devcd://context/agent-handoff-packet")

    assert body["schema_version"] == "1"
    assert body["surface"] == "coding-agent"
    assert body["goal"] == "Add agent handoff MCP resource"
    assert "policy_summary" in body
    assert body["policy_summary"]["allowed"] is True
    assert "withheld_context_summary" in body


def test_mcp_server_agent_handoff_packet_matches_cli_contract_fields(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"current_goal": "Continue after chat context loss"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="fix_attempt",
            timestamp=datetime(2026, 5, 5, 10, 1, tzinfo=UTC),
            payload={"summary": "Only changed the Markdown handoff"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 5, 10, 2, tzinfo=UTC),
            payload={
                "reason": "JSON handoff still omits stale attempt guidance",
                "suggested_next_action": "Add stale attempt guidance to the JSON contract",
            },
        )
    )

    body = read_resource(server, "devcd://context/agent-handoff-packet")

    assert body["surface"] == "coding-agent"
    assert body["goal"] == "Continue after chat context loss"
    assert body["last_failure"] == "JSON handoff still omits stale attempt guidance"
    assert body["do_not_repeat"] == [
        "Do not repeat the last attempted fix unchanged: Only changed the Markdown handoff"
    ]
    assert body["suggested_next_action"] == "Add stale attempt guidance to the JSON contract"
    assert set(body.keys()) >= {
        "schema_version",
        "brief_id",
        "surface",
        "goal",
        "last_attempt",
        "last_failure",
        "why_attempt_failed",
        "do_not_repeat",
        "suggested_next_action",
        "policy_summary",
        "withheld_context_summary",
        "context_quality_notes",
    }


def test_mcp_server_agent_handoff_packet_withholds_sensitive_payloads(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"title": "Secret API key: sk-supersecret"},
            sensitivity="sensitive",
        )
    )

    response_text = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "resources/read",
            "params": {"uri": "devcd://context/agent-handoff-packet"},
        }
    )
    assert response_text is not None
    raw = response_text["result"]["contents"][0]["text"]

    assert "sk-supersecret" not in raw
    assert "Secret API key" not in raw


def test_mcp_server_agent_handoff_packet_listed_in_resources(tmp_path) -> None:
    server, _state_engine = build_mcp_server(tmp_path)

    resources_response = server.handle_message(
        {"jsonrpc": "2.0", "id": 11, "method": "resources/list"}
    )
    assert resources_response is not None
    uris = [r["uri"] for r in resources_response["result"]["resources"]]
    assert "devcd://context/agent-handoff-packet" in uris
    names = [r["name"] for r in resources_response["result"]["resources"]]
    assert "agent_handoff_packet" in names


def test_mcp_server_recent_timeline_is_chronological(tmp_path) -> None:
    server, state_engine = build_mcp_server(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 5, 9, 0, tzinfo=UTC),
            payload={"branch": "feat/first"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.GIT,
            type="branch_change",
            timestamp=datetime(2026, 5, 5, 10, 0, tzinfo=UTC),
            payload={"branch": "feat/second"},
        )
    )

    body = read_resource(server, "devcd://context/recent-timeline")

    timeline = body["recent_timeline"]
    assert isinstance(timeline, list)
    assert len(timeline) == 2
    assert timeline[0]["payload"]["branch"] == "feat/first"
    assert timeline[1]["payload"]["branch"] == "feat/second"


def test_mcp_server_policy_summary_contains_expected_fields(tmp_path) -> None:
    server, _state_engine = build_mcp_server(tmp_path)

    body = read_resource(server, "devcd://context/policy-summary")

    assert "allowed" in body
    assert "operation" in body
    assert "reason" in body
    assert "included_sources" in body
    assert "withheld_sources" in body
