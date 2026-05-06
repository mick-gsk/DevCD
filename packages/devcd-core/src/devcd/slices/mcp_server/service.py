from __future__ import annotations

import json
from typing import Any, TextIO

from devcd.slices.agentic_context.service import AgenticContextService
from devcd.slices.ambient_context.models import AgentContextSurface, SurfaceKind
from devcd.slices.ambient_context.service import (
    AmbientContextService,
    render_context_brief_json,
    render_continuity_packet_json,
)
from devcd.slices.events.ledger import EventLedger
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.policy_layer.service import PolicyEngine

JsonObject = dict[str, Any]

READ_ONLY_RESOURCE_URIS: tuple[str, ...] = (
    "devcd://context/brief",
    "devcd://context/work-state",
    "devcd://context/recent-events",
    "devcd://context/policy-decisions",
    "devcd://context/withheld-context",
    "devcd://context/agent-handoff-packet",
    "devcd://context/continuity-packet",
    "devcd://context/action-packet",
    "devcd://context/session-contract",
    "devcd://context/recent-timeline",
    "devcd://context/policy-summary",
)

_NO_MUTATION_RESOURCE_NOTE = " No MCP tools, prompts, or mutations are exposed."

_RESOURCE_METADATA: dict[str, dict[str, str]] = {
    "devcd://context/brief": {
        "name": "context_brief",
        "description": "Policy-filtered DevCD context brief for local MCP clients.",
    },
    "devcd://context/work-state": {
        "name": "work_state",
        "description": "Current policy-filtered DevCD work state.",
    },
    "devcd://context/recent-events": {
        "name": "recent_events",
        "description": "Recent local ledger events visible under policy.",
    },
    "devcd://context/policy-decisions": {
        "name": "policy_decisions",
        "description": "Recent local policy decisions visible under policy.",
    },
    "devcd://context/withheld-context": {
        "name": "withheld_context",
        "description": "Safe summaries for context withheld by policy.",
    },
    "devcd://context/agent-handoff-packet": {
        "name": "agent_handoff_packet",
        "description": (
            "Agent continuity handoff packet (coding-agent surface). "
            "Same JSON contract as 'devcd context handoff-demo --json'. "
            "Includes goal, resurrection context, blockers, and withheld-context summary. "
            "No sensitive payloads."
        ),
    },
    "devcd://context/continuity-packet": {
        "name": "continuity_packet",
        "description": (
            "Domain-neutral policy-filtered continuity packet (developer pack by default). "
            "Structured ContinuityPacket model: intent, artifacts, attempts, blockers, "
            "do_not_repeat, suggested_next_steps, and withheld-context metadata. "
            "No sensitive payloads."
        ),
    },
    "devcd://context/action-packet": {
        "name": "action_packet",
        "description": (
            "Agentic Action Packet for the next local agent run. "
            "Includes current goal, next action, evidence, and policy summary. "
            "No sensitive payloads."
        ),
    },
    "devcd://context/session-contract": {
        "name": "session_contract",
        "description": (
            "Read-only next-session contract with context references, budget, "
            "verification command, and clean-state guidance. No sensitive payloads."
        ),
    },
    "devcd://context/recent-timeline": {
        "name": "recent_timeline",
        "description": (
            "Chronological (oldest-first) timeline of recent policy-visible events. "
            "Useful for understanding the narrative of what happened."
        ),
    },
    "devcd://context/policy-summary": {
        "name": "policy_summary",
        "description": (
            "Concise policy summary: allowed/withheld sources and data classes "
            "for the current work state."
        ),
    },
}


class ReadOnlyMCPServer:
    def __init__(
        self,
        *,
        ambient_context_service: AmbientContextService,
        state_engine: StateEngine,
        event_ledger: EventLedger,
        policy_engine: PolicyEngine,
        agentic_context_service: AgenticContextService | None = None,
    ) -> None:
        self._ambient_context_service = ambient_context_service
        self._state_engine = state_engine
        self._event_ledger = event_ledger
        self._policy_engine = policy_engine
        self._agentic_context_service = agentic_context_service or AgenticContextService(
            ambient_context_service=ambient_context_service,
            policy_engine=policy_engine,
        )

    def handle_message(self, message: JsonObject) -> JsonObject | None:
        request_id = message.get("id")
        method = message.get("method")
        if request_id is None:
            return None
        if not isinstance(method, str):
            return self._error(request_id, -32600, "invalid JSON-RPC request")

        if method == "initialize":
            return self._result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"resources": {}},
                    "serverInfo": {"name": "devcd", "version": "0.1.0"},
                },
            )
        if method == "resources/list":
            return self._result(request_id, {"resources": self._list_resources()})
        if method == "resources/read":
            uri = self._resource_uri(message.get("params"))
            if uri is None:
                return self._error(request_id, -32602, "resource uri is required")
            if uri not in READ_ONLY_RESOURCE_URIS:
                return self._error(request_id, -32602, f"unknown resource: {uri}")
            return self._result(request_id, {"contents": [self._resource_content(uri)]})
        if method == "tools/list":
            return self._result(request_id, {"tools": []})
        if method == "prompts/list":
            return self._result(request_id, {"prompts": []})
        if method == "ping":
            return self._result(request_id, {})
        return self._error(request_id, -32601, f"unsupported method: {method}")

    def _list_resources(self) -> list[JsonObject]:
        resources: list[JsonObject] = []
        for uri in READ_ONLY_RESOURCE_URIS:
            metadata = _RESOURCE_METADATA[uri]
            resources.append(
                {
                    "uri": uri,
                    "name": metadata["name"],
                    "description": metadata["description"] + _NO_MUTATION_RESOURCE_NOTE,
                    "mimeType": "application/json",
                }
            )
        return resources

    def _resource_uri(self, params: object) -> str | None:
        if not isinstance(params, dict):
            return None
        uri = params.get("uri")
        return uri if isinstance(uri, str) and uri else None

    def _resource_content(self, uri: str) -> JsonObject:
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": self._resource_text(uri),
        }

    def _resource_text(self, uri: str) -> str:
        if uri == "devcd://context/brief":
            return self._json_text(
                self._ambient_context_service.create_context_brief(self._mcp_surface()).model_dump(
                    mode="json"
                )
            )
        if uri == "devcd://context/work-state":
            return self._json_text(
                self._ambient_context_service.get_work_state().model_dump(mode="json")
            )
        if uri == "devcd://context/recent-events":
            return self._json_text({"recent_events": self._recent_events()})
        if uri == "devcd://context/policy-decisions":
            return self._json_text({"policy_decisions": self._policy_decisions()})
        if uri == "devcd://context/withheld-context":
            brief = self._ambient_context_service.create_context_brief(self._mcp_surface())
            return self._json_text(
                {
                    "withheld_context": [
                        item.model_dump(mode="json") for item in brief.withheld_context
                    ],
                    "policy_decision": brief.policy_decision.model_dump(mode="json"),
                }
            )
        if uri == "devcd://context/agent-handoff-packet":
            surface = AgentContextSurface(kind=SurfaceKind.CODING_AGENT, name="devcd-mcp-handoff")
            brief = self._ambient_context_service.create_context_brief(surface)
            return render_context_brief_json(brief)
        if uri == "devcd://context/continuity-packet":
            packet = self._ambient_context_service.create_continuity_packet(
                self._mcp_surface(),
                context_pack="developer",
                include_empty_guidance=True,
            )
            return render_continuity_packet_json(packet)
        if uri == "devcd://context/action-packet":
            action_packet = self._agentic_context_service.create_action_packet(
                surface="mcp",
                context_pack="developer",
            )
            return self._json_text(action_packet.model_dump(mode="json"))
        if uri == "devcd://context/session-contract":
            packet = self._ambient_context_service.create_continuity_packet(
                self._mcp_surface(),
                context_pack="developer",
                include_empty_guidance=True,
            )
            return self._json_text(
                {
                    "session_contract": packet.session_contract.model_dump(mode="json")
                    if packet.session_contract is not None
                    else None,
                    "context_budget": packet.context_budget.model_dump(mode="json"),
                    "context_references": [
                        reference.model_dump(mode="json")
                        for reference in packet.context_references
                    ],
                    "policy_summary": packet.policy_decision.reason,
                }
            )
        if uri == "devcd://context/recent-timeline":
            return self._json_text({"recent_timeline": self._recent_timeline()})
        if uri == "devcd://context/policy-summary":
            work_state = self._ambient_context_service.get_work_state()
            return self._json_text(work_state.policy_summary.model_dump(mode="json"))
        raise ValueError(f"unknown resource: {uri}")

    def _mcp_surface(self) -> AgentContextSurface:
        return AgentContextSurface(kind=SurfaceKind.MCP, name="devcd-mcp")

    def _recent_events(self) -> list[JsonObject]:
        recent_events: list[JsonObject] = []
        for event, _decision in reversed(self._event_ledger.read_records()):
            if not self._is_visible_event(event.source.value, event.data_class):
                continue
            recent_events.append(event.model_dump(mode="json"))
            if len(recent_events) == 20:
                break
        return recent_events

    def _policy_decisions(self) -> list[JsonObject]:
        policy_decisions: list[JsonObject] = []
        for event, decision in reversed(self._event_ledger.read_records()):
            data_class = decision.data_class or event.data_class
            source = decision.source or event.source.value
            if not self._is_visible_event(source, data_class):
                continue
            policy_decisions.append(decision.model_dump(mode="json"))
            if len(policy_decisions) == 20:
                break
        return policy_decisions

    def _recent_timeline(self) -> list[JsonObject]:
        """Chronological (oldest-first) timeline of recent policy-visible events."""
        all_visible: list[JsonObject] = []
        for event, _decision in self._event_ledger.read_records():
            if not self._is_visible_event(event.source.value, event.data_class):
                continue
            all_visible.append(event.model_dump(mode="json"))
        return all_visible[-20:]

    def _is_visible_event(self, source: str | None, data_class: str) -> bool:
        if not self._state_engine.is_source_visible(source):
            return False
        decision = self._policy_engine.decide_context_export(surface="mcp", data_class=data_class)
        return decision.allowed

    def _json_text(self, value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def _result(self, request_id: object, result: JsonObject) -> JsonObject:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error(self, request_id: object, code: int, message: str) -> JsonObject:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def serve_stdio(server: ReadOnlyMCPServer, input_stream: TextIO, output_stream: TextIO) -> None:
    for line in input_stream:
        if not line.strip():
            continue
        response = _handle_stdio_line(server, line)
        if response is None:
            continue
        output_stream.write(json.dumps(response, sort_keys=True, separators=(",", ":")))
        output_stream.write("\n")
        output_stream.flush()


def _handle_stdio_line(server: ReadOnlyMCPServer, line: str) -> JsonObject | None:
    try:
        raw_message = json.loads(line)
    except json.JSONDecodeError:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
    if not isinstance(raw_message, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "invalid request"},
        }
    return server.handle_message(raw_message)
