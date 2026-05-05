from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, cast
from urllib.parse import quote, urlparse
from uuid import uuid4

import tomli_w
import typer
import uvicorn

from devcd.host import create_app
from devcd.kernel.settings import DevCDSettings
from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    ContextFeedback,
    ContextFeedbackKind,
    ContextQualityReport,
    DetailLevel,
    SurfaceKind,
)
from devcd.slices.ambient_context.service import (
    AmbientContextService,
    render_context_brief_json,
    render_context_brief_markdown,
)
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource
from devcd.slices.events.recipes import PytestFailureRecipeInput, events_from_pytest_failure
from devcd.slices.git_source.service import GitEventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.mcp_server.service import ReadOnlyMCPServer, serve_stdio
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine

app = typer.Typer(help="DevCD local context daemon.")
context_app = typer.Typer(help="Inspect ambient developer context.")
mcp_app = typer.Typer(help="Serve read-only DevCD context through MCP.")
policy_app = typer.Typer(help="Explain and simulate local policy decisions.")
recipe_app = typer.Typer(help="Convert local workflow reports into DevCD events.")
app.add_typer(context_app, name="context")
app.add_typer(mcp_app, name="mcp")
app.add_typer(policy_app, name="policy")
app.add_typer(recipe_app, name="recipe")

_LOCAL_TOKEN_PATH = Path(".devcd") / "token"
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@app.command()
def init(
    path: Annotated[Path, typer.Option("--path", help="Config file to create.")] = Path(
        "devcd.toml"
    ),
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config.")] = False,
) -> None:
    """Create a local DevCD config file."""
    if path.exists() and not force:
        raise typer.BadParameter(f"{path} already exists; pass --force to overwrite it")

    settings = DevCDSettings()
    path.write_text(
        tomli_w.dumps({"devcd": settings.to_config_dict()}),
        encoding="utf-8",
    )
    typer.echo(f"Wrote {path}")


@app.command()
def serve(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    host: Annotated[str | None, typer.Option("--host", help="Host override.")] = None,
    port: Annotated[int | None, typer.Option("--port", help="Port override.")] = None,
) -> None:
    """Run the local DevCD daemon API."""
    _run_daemon(config=config, host=host, port=port)


@app.command("run")
def run_daemon(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    host: Annotated[str | None, typer.Option("--host", help="Host override.")] = None,
    port: Annotated[int | None, typer.Option("--port", help="Port override.")] = None,
) -> None:
    """Run the local DevCD daemon API."""
    _run_daemon(config=config, host=host, port=port)


def _run_daemon(config: Path | None, host: str | None, port: int | None) -> None:
    settings = DevCDSettings.load(config)
    uvicorn.run(create_app(settings), host=host or settings.host, port=port or settings.port)


@app.command()
def status(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", help="DevCD daemon state endpoint."),
    ] = "http://127.0.0.1:8765/state",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Print local DevCD runtime readiness."""
    report = _build_status_report(config=config, endpoint=endpoint, token=token)
    typer.echo(_render_status_report(report))


@app.command()
def doctor(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", help="DevCD daemon state endpoint."),
    ] = "http://127.0.0.1:8765/state",
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON output."),
    ] = False,
) -> None:
    """Run local DevCD operational readiness checks."""
    report = _build_doctor_report(config=config, endpoint=endpoint)
    typer.echo(
        json.dumps(report, indent=2, sort_keys=True)
        if output_json
        else _render_doctor_report(report)
    )


@app.command()
def event(
    source: Annotated[str, typer.Argument(help="Event source, e.g. ide/git/task.")],
    event_type: Annotated[str, typer.Argument(help="Normalized event type.")],
    payload: Annotated[str, typer.Option("--payload", help="JSON object payload.")] = "{}",
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD daemon endpoint.")
    ] = "http://127.0.0.1:8765/event",
    sensitivity: Annotated[
        str, typer.Option("--sensitivity", help="normal or sensitive.")
    ] = "normal",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Submit a normalized event to a running daemon."""
    parsed_payload = json.loads(payload)
    if not isinstance(parsed_payload, dict):
        raise typer.BadParameter("--payload must be a JSON object")

    response = _post_event(
        endpoint=endpoint,
        event={
            "source": source,
            "type": event_type,
            "payload": parsed_payload,
            "sensitivity": sensitivity,
        },
        token=token,
    )
    typer.echo(response)


@app.command("git-snapshot")
def git_snapshot(
    repo: Annotated[Path, typer.Option("--repo", help="Git repository to inspect.")] = Path("."),
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD daemon endpoint.")
    ] = "http://127.0.0.1:8765/event",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Submit branch and latest-commit events for a Git repository."""
    events = GitEventSource().collect_snapshot_events(repo)
    if not events:
        typer.echo("No git events collected")
        return

    for git_event in events:
        typer.echo(
            _post_event(
                endpoint=endpoint,
                event=git_event.model_dump(mode="json"),
                token=token,
            )
        )


@context_app.callback()
def context() -> None:
    """Ambient context commands."""


@mcp_app.callback()
def mcp() -> None:
    """MCP commands."""


@policy_app.callback()
def policy() -> None:
    """Policy commands."""


@recipe_app.callback()
def recipe() -> None:
    """Event recipe commands."""


@recipe_app.command("pytest-failure")
def recipe_pytest_failure(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="JSON pytest failure report to convert."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional JSONL output path."),
    ] = None,
) -> None:
    """Convert a local pytest failure report into DevCD JSONL events."""
    report = PytestFailureRecipeInput.model_validate_json(input_path.read_text(encoding="utf-8"))
    jsonl = "\n".join(event.model_dump_json() for event in events_from_pytest_failure(report))
    jsonl = f"{jsonl}\n"
    if output is not None:
        output.write_text(jsonl, encoding="utf-8")
        typer.echo(f"Wrote {output}")
        return
    typer.echo(jsonl, nl=False)


@policy_app.command("simulate")
def policy_simulate(
    surface: Annotated[str, typer.Option("--surface", help="Context surface to evaluate.")],
    event: Annotated[Path, typer.Option("--event", help="JSON or JSONL file with one event.")],
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON output."),
    ] = False,
) -> None:
    """Simulate policy decisions for an event without mutating state."""
    policy_engine = PolicyEngine.from_settings(DevCDSettings.load(config))
    report = policy_engine.simulate_event(surface=surface, event=_read_event_file(event))
    typer.echo(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
        if output_json
        else _render_policy_simulation(report.model_dump(mode="json"))
    )


@policy_app.command("explain")
def policy_explain(
    decision_id: Annotated[str, typer.Argument(help="Policy decision identifier to explain.")],
    ledger: Annotated[
        Path,
        typer.Option("--ledger", help="Local DevCD event ledger to inspect."),
    ] = Path(".devcd/events.jsonl"),
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON output."),
    ] = False,
) -> None:
    """Explain a recorded policy decision from the local ledger."""
    explanation = _explain_ledger_decision(decision_id=decision_id, ledger_path=ledger)
    typer.echo(
        json.dumps(explanation, indent=2, sort_keys=True)
        if output_json
        else _render_policy_explanation(explanation)
    )


@mcp_app.command("serve")
def mcp_serve(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
    token: Annotated[
        str | None,
        typer.Option("--token", help="Local MCP bearer token for process start."),
    ] = None,
) -> None:
    """Run the local read-only DevCD MCP stdio server."""
    settings = DevCDSettings.load(config)
    _ensure_mcp_token(settings=settings, token=token)
    serve_stdio(_build_mcp_server(settings), sys.stdin, sys.stdout)


@context_app.command("state")
def context_state(
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient work-state endpoint.")
    ] = "http://127.0.0.1:8765/context/work-state",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Print the current ambient work state."""
    typer.echo(_get_json(endpoint=endpoint, token=token))


@context_app.command("brief")
def context_brief(
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient context brief endpoint.")
    ] = "http://127.0.0.1:8765/context/brief",
    surface: Annotated[str, typer.Option("--surface", help="Context surface kind.")] = "cli",
    detail: Annotated[
        str, typer.Option("--detail", help="minimal, standard, or diagnostic.")
    ] = "standard",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Print a policy-filtered agent context brief."""
    typer.echo(
        _post_json(
            endpoint=endpoint,
            body={"kind": surface, "name": "devcd-cli", "detail_level": detail},
            token=token,
        )
    )


@context_app.command("feedback")
def context_feedback(
    brief_id: Annotated[str, typer.Argument(help="Handoff brief identifier.")],
    kind: Annotated[str, typer.Option("--kind", help="Feedback kind.")],
    note: Annotated[str, typer.Option("--note", help="Local feedback note.")],
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
) -> None:
    """Store local feedback for a handoff brief."""
    try:
        feedback = _build_local_context_service(config).record_feedback(
            brief_id=brief_id,
            kind=_context_feedback_kind(kind),
            note=note,
        )
    except PermissionError as error:
        typer.echo(f"Failed to store feedback: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(_render_feedback_result(feedback))


@context_app.command("quality")
def context_quality(
    config: Annotated[Path | None, typer.Option("--config", help="Config file to load.")] = None,
) -> None:
    """Print locally stored handoff feedback."""
    service = _build_local_context_service(config)
    typer.echo(_render_context_quality(service.get_context_quality()))


@context_app.command("handoff-demo")
def context_handoff_demo(
    events: Annotated[Path, typer.Option("--events", help="JSONL file with DevCD events.")],
    surface: Annotated[str, typer.Option("--surface", help="Context surface kind.")] = "cli",
    detail: Annotated[
        str, typer.Option("--detail", help="minimal, standard, or diagnostic.")
    ] = "standard",
    output_json: Annotated[
        bool, typer.Option("--json", help="Emit JSON contract instead of Markdown.")
    ] = False,
) -> None:
    """Generate a read-only agent handoff brief from local JSONL events."""
    with TemporaryDirectory() as temporary_directory:
        service, state_engine = _build_demo_context_service(Path(temporary_directory))
        for event in _read_jsonl_events(events):
            state_engine.accept_event(event)
        brief = service.create_context_brief(
            AgentContextSurface(
                kind=_surface_kind(surface),
                name="devcd-cli",
                detail_level=_detail_level(detail),
            )
        )
        brief = brief.model_copy(update={"id": "demo-handoff-brief"})
        if output_json:
            typer.echo(render_context_brief_json(brief))
        else:
            typer.echo(render_context_brief_markdown(brief))


@context_app.command("dismiss-suggestion")
def context_dismiss_suggestion(
    suggestion_id: Annotated[str, typer.Argument(help="suggestion-id to dismiss")],
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient context API endpoint.")
    ] = "http://127.0.0.1:8765/context",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Dismiss a proactive suggestion and start its cooldown."""
    url = f"{endpoint}/suggestions/{quote(suggestion_id, safe='')}/dismiss"
    typer.echo(_post_json(endpoint=url, body={}, token=token))


@context_app.command("memory")
def context_memory(
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient context memory endpoint.")
    ] = "http://127.0.0.1:8765/context/memory",
    scope: Annotated[
        str | None,
        typer.Option("--scope", help="working, episodic, or semantic."),
    ] = None,
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Print retained context memory visible under policy."""
    url = endpoint if scope is None else f"{endpoint}?scope={quote(scope, safe='')}"
    typer.echo(_get_json(endpoint=url, token=token))


@context_app.command("memory-correct")
def context_memory_correct(
    item_id: Annotated[str, typer.Argument(help="item-id to correct")],
    summary: Annotated[str, typer.Argument(help="Corrected memory summary")],
    reason: Annotated[str, typer.Option("--reason", help="Reason for the correction.")],
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient context memory endpoint.")
    ] = "http://127.0.0.1:8765/context/memory",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Correct a retained context memory item."""
    url = f"{endpoint}/{quote(item_id, safe='')}"
    typer.echo(_patch_json(endpoint=url, body={"summary": summary, "reason": reason}, token=token))


@context_app.command("memory-delete")
def context_memory_delete(
    item_id: Annotated[str, typer.Argument(help="item-id to delete")],
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD ambient context memory endpoint.")
    ] = "http://127.0.0.1:8765/context/memory",
    token: Annotated[str | None, typer.Option("--token", help="Local API bearer token.")] = None,
) -> None:
    """Delete a retained context memory item."""
    url = f"{endpoint}/{quote(item_id, safe='')}"
    typer.echo(_delete_json(endpoint=url, token=token))


def _build_status_report(
    *,
    config: Path | None,
    endpoint: str,
    token: str | None,
) -> dict[str, Any]:
    config_path = _readiness_config_path(config)
    config_exists = config_path.exists()
    settings = DevCDSettings.load(config)
    token_source, resolved_token = _readiness_token_source(settings, endpoint, token)
    daemon = _probe_daemon(endpoint=endpoint, token=resolved_token)
    records = EventLedger(settings.ledger_path).read_records()

    return {
        "config_path": str(config_path),
        "config_exists": config_exists,
        "endpoint": endpoint,
        "daemon": daemon,
        "token_source": token_source,
        "workspace": str(Path.cwd()),
        "events_count": len(records),
        "last_event_timestamp": _last_event_timestamp(records),
        "active_goal": _latest_payload_string(
            records,
            event_type="goal_update",
            key="current_goal",
        ),
        "current_branch": _latest_payload_string(records, event_type="branch_change", key="branch"),
        "policy_mode": _policy_mode(settings),
        "policy_decision_count": len(records),
        "memory_path": str(settings.ledger_path),
        "memory_available": settings.runtime_dir.exists(),
        "handoff_available": _handoff_available(settings),
        "mcp_available": True,
        "next_command": _next_status_command(
            config_exists=config_exists,
            token_source=token_source,
            daemon_reachable=bool(daemon["reachable"]),
            events_count=len(records),
        ),
    }


def _build_doctor_report(*, config: Path | None, endpoint: str) -> dict[str, Any]:
    config_path = _readiness_config_path(config)
    settings = DevCDSettings.load(config)
    token_source, resolved_token = _readiness_token_source(settings, endpoint, None)
    daemon = _probe_daemon(endpoint=endpoint, token=resolved_token)
    state_status = _state_engine_readiness(settings)
    checks = [
        _doctor_check(
            "config_exists",
            "pass" if config_path.exists() else "warn",
            f"Config found at {config_path}" if config_path.exists() else "No devcd.toml found",
            {"path": str(config_path)},
            "devcd init" if not config_path.exists() else "devcd status",
        ),
        _doctor_check(
            "token_exists",
            "pass" if token_source != "missing" else "warn",
            f"Token source: {token_source}"
            if token_source != "missing"
            else "No local token found",
            {"source": token_source},
            "devcd run" if token_source == "missing" else "devcd status",
        ),
        _doctor_check(
            "daemon_reachable",
            "pass" if daemon["reachable"] else "warn",
            "Daemon state endpoint is reachable"
            if daemon["reachable"]
            else "Daemon is not reachable",
            daemon,
            "devcd run" if not daemon["reachable"] else "devcd context brief --surface cli",
        ),
        _doctor_check(
            "event_ingestion_or_demo",
            "pass" if daemon["reachable"] or _sample_events_path().exists() else "warn",
            "Daemon is reachable or local handoff demo events exist",
            {"daemon_reachable": daemon["reachable"], "demo_events": str(_sample_events_path())},
            "devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl",
        ),
        _doctor_check(
            "state_engine_state",
            "pass" if state_status["has_state"] else "warn",
            "State engine has local state" if state_status["has_state"] else "No local state found",
            state_status,
            'devcd event ide file_focus --payload \'{"path":"src/app.py"}\'',
        ),
        _policy_sensitive_denial_check(settings),
        _sample_events_valid_check(),
        _handoff_demo_check(),
        _docs_commands_check(),
    ]
    return {
        "summary": {
            "status": "ready"
            if all(check["status"] == "pass" for check in checks)
            else "attention",
            "remote_export": "enabled" if settings.allow_remote_export else "disabled",
            "telemetry": "not implemented",
            "workspace": str(Path.cwd()),
        },
        "checks": checks,
    }


def _doctor_check(
    check_id: str,
    status_value: str,
    summary: str,
    details: dict[str, Any],
    next_step: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status_value,
        "summary": summary,
        "details": details,
        "next_step": next_step,
    }


def _policy_sensitive_denial_check(settings: DevCDSettings) -> dict[str, Any]:
    event = DevEvent(
        source=EventSource.NOTES,
        type="note_update",
        payload={"title": "Synthetic sensitive readiness sample"},
        sensitivity=EventSensitivity.SENSITIVE,
    )
    decision = PolicyEngine.from_settings(settings).decide_observation(event)
    return _doctor_check(
        "policy_sensitive_denial",
        "pass" if not decision.allowed else "fail",
        "Sensitive sample is denied" if not decision.allowed else "Sensitive sample was allowed",
        {"decision": decision.kind.value, "reason": decision.reason},
        "Review allowed_data_classes and sensitivity policy"
        if decision.allowed
        else "devcd policy simulate --surface coding-agent --event <file>",
    )


def _sample_events_valid_check() -> dict[str, Any]:
    sample_path = _sample_events_path()
    try:
        events = _read_jsonl_events(sample_path)
    except (OSError, typer.BadParameter, ValueError) as error:
        return _doctor_check(
            "sample_events_valid",
            "fail",
            "Agent handoff sample events are not valid",
            {"path": str(sample_path), "error": str(error)},
            "Fix examples/agent-handoff/sample-events.jsonl",
        )
    return _doctor_check(
        "sample_events_valid",
        "pass",
        "Agent handoff sample events are valid",
        {"path": str(sample_path), "events_count": len(events)},
        "devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl",
    )


def _handoff_demo_check() -> dict[str, Any]:
    sample_path = _sample_events_path()
    try:
        with TemporaryDirectory() as temporary_directory:
            service, state_engine = _build_demo_context_service(Path(temporary_directory))
            for event in _read_jsonl_events(sample_path):
                state_engine.accept_event(event)
            brief = service.create_context_brief(
                AgentContextSurface(kind=SurfaceKind.CLI, name="devcd-doctor")
            )
    except (OSError, typer.BadParameter, ValueError) as error:
        return _doctor_check(
            "handoff_demo",
            "fail",
            "Context handoff demo could not be generated",
            {"path": str(sample_path), "error": str(error)},
            "devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl",
        )
    return _doctor_check(
        "handoff_demo",
        "pass",
        "Context handoff demo can be generated",
        {"path": str(sample_path), "brief_id": brief.id},
        "devcd context handoff-demo --events examples/agent-handoff/sample-events.jsonl",
    )


def _docs_commands_check() -> dict[str, Any]:
    docs_path = Path("docs/getting-started.md")
    try:
        content = docs_path.read_text(encoding="utf-8")
    except OSError as error:
        return _doctor_check(
            "docs_commands",
            "warn",
            "Getting Started docs could not be read",
            {"path": str(docs_path), "error": str(error)},
            "Check docs/getting-started.md",
        )
    missing = [command for command in ("devcd status", "devcd doctor") if command not in content]
    return _doctor_check(
        "docs_commands",
        "pass" if not missing else "warn",
        "Docs mention readiness commands" if not missing else "Docs are missing readiness commands",
        {"path": str(docs_path), "missing": missing},
        "Update docs/getting-started.md" if missing else "devcd doctor",
    )


def _readiness_config_path(config: Path | None) -> Path:
    if config is not None:
        return config
    env_config = os.environ.get("DEVCD_CONFIG", "").strip()
    return Path(env_config) if env_config else Path("devcd.toml")


def _readiness_token_source(
    settings: DevCDSettings,
    endpoint: str,
    token: str | None,
) -> tuple[str, str | None]:
    if token:
        return "option", token
    if not _is_loopback_endpoint(endpoint):
        return "not sent to non-loopback endpoint", None
    env_token = os.environ.get("DEVCD_TOKEN", "").strip()
    if env_token:
        return "env:DEVCD_TOKEN", env_token
    if settings.api_token:
        return "config:api_token", settings.api_token

    for token_path in (settings.runtime_dir / "token", _LOCAL_TOKEN_PATH):
        if token_path.exists():
            file_token = token_path.read_text(encoding="utf-8").strip()
            if file_token:
                return f"file:{token_path}", file_token
    return "missing", None


def _probe_daemon(endpoint: str, token: str | None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            return {
                "endpoint": endpoint,
                "reachable": True,
                "authorized": False,
                "reason": f"HTTP {error.code}",
            }
        return {
            "endpoint": endpoint,
            "reachable": False,
            "authorized": False,
            "reason": f"HTTP {error.code}",
        }
    except (TimeoutError, urllib.error.URLError) as error:
        return {
            "endpoint": endpoint,
            "reachable": False,
            "authorized": False,
            "reason": str(error),
        }

    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = None
    return {"endpoint": endpoint, "reachable": True, "authorized": True, "state": parsed}


def _state_engine_readiness(settings: DevCDSettings) -> dict[str, Any]:
    policy_engine = PolicyEngine.from_settings(settings)
    memory_store = MemoryStore.with_ttl_seconds(settings.working_memory_ttl_seconds)
    event_ledger = EventLedger(settings.ledger_path)
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    state_engine.rebuild_from_ledger()
    state = state_engine.state
    records = event_ledger.read_records()
    return {
        "has_state": bool(state.current_goal or state.recent_actions or state.source_active_map),
        "events_count": len(records),
        "last_event": _last_event_timestamp(records),
        "recent_actions": len(state.recent_actions),
    }


def _last_event_timestamp(records: list[tuple[DevEvent, Any]]) -> str | None:
    if not records:
        return None
    return max(event.timestamp for event, _decision in records).isoformat()


def _latest_payload_string(
    records: list[tuple[DevEvent, Any]],
    *,
    event_type: str,
    key: str,
) -> str | None:
    for event, _decision in reversed(records):
        if event.type != event_type:
            continue
        value = event.payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _policy_mode(settings: DevCDSettings) -> str:
    return (
        f"observe={'yes' if settings.allow_observation else 'no'}, "
        f"store={'yes' if settings.allow_local_storage else 'no'}, "
        f"remote_export={'yes' if settings.allow_remote_export else 'no'}, "
        f"actions={'yes' if settings.allow_actions else 'no'}"
    )


def _handoff_available(settings: DevCDSettings) -> bool:
    policy_engine = PolicyEngine.from_settings(settings)
    memory_store = MemoryStore.with_ttl_seconds(settings.working_memory_ttl_seconds)
    state_engine = StateEngine(policy_engine, memory_store, EventLedger.disabled())
    service = AmbientContextService(state_engine, memory_store, policy_engine)
    brief = service.create_context_brief(AgentContextSurface(kind=SurfaceKind.CLI, name="status"))
    return bool(brief.id)


def _next_status_command(
    *,
    config_exists: bool,
    token_source: str,
    daemon_reachable: bool,
    events_count: int,
) -> str:
    if not config_exists:
        return "devcd init"
    if token_source == "missing" or not daemon_reachable:
        return "devcd run"
    if events_count == 0:
        return 'devcd event ide file_focus --payload \'{"path":"src/app.py"}\''
    return "devcd context brief --surface cli --detail standard"


def _sample_events_path() -> Path:
    return Path("examples/agent-handoff/sample-events.jsonl")


def _render_status_report(report: dict[str, Any]) -> str:
    daemon = report["daemon"]
    daemon_status = "reachable" if daemon["reachable"] else "unreachable"
    lines = [
        "DevCD status",
        f"Daemon: {daemon_status} ({report['endpoint']})",
        f"Auth token: {report['token_source']}",
        f"Workspace: {report['workspace']}",
        f"Events: {report['events_count']}",
        f"Last event: {report['last_event_timestamp'] or 'none'}",
        f"Active goal: {report['active_goal'] or 'none'}",
        f"Current branch: {report['current_branch'] or 'unknown'}",
        f"Policy: {report['policy_mode']} ({report['policy_decision_count']} decisions)",
        (
            f"Memory: {'available' if report['memory_available'] else 'missing'} "
            f"({report['memory_path']})"
        ),
        f"Handoff: {'available' if report['handoff_available'] else 'unavailable'}",
        f"MCP: {'available' if report['mcp_available'] else 'unavailable'}",
        f"Next: {report['next_command']}",
    ]
    return "\n".join(lines)


def _render_doctor_report(report: dict[str, Any]) -> str:
    lines = ["DevCD doctor"]
    for check in report["checks"]:
        lines.append(f"{check['id']}: {check['status']} - {check['summary']}")
    next_steps = [check["next_step"] for check in report["checks"] if check["status"] != "pass"]
    if next_steps:
        lines.extend(["", "Next steps"])
        for next_step in dict.fromkeys(next_steps):
            lines.append(f"- {next_step}")
    else:
        lines.extend(["", "Next steps", "- devcd status"])
    return "\n".join(lines)


def _post_event(endpoint: str, event: dict[str, Any], token: str | None = None) -> str:
    body = json.dumps(event).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    resolved_token = _resolve_local_api_token(endpoint=endpoint, token=token)
    if resolved_token is not None:
        headers["Authorization"] = f"Bearer {resolved_token}"
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to submit event: {error}", err=True)
        raise typer.Exit(1) from error


def _build_demo_context_service(
    temporary_directory: Path,
) -> tuple[AmbientContextService, StateEngine]:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    ledger_path = temporary_directory / "events.jsonl"
    event_ledger = EventLedger(ledger_path)
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    service = AmbientContextService(state_engine, memory_store, policy_engine)
    return service, state_engine


def _build_mcp_server(settings: DevCDSettings) -> ReadOnlyMCPServer:
    policy_engine = PolicyEngine.from_settings(settings)
    memory_store = MemoryStore.with_ttl_seconds(settings.working_memory_ttl_seconds)
    event_ledger = EventLedger(settings.ledger_path)
    state_engine = StateEngine(
        policy_engine=policy_engine,
        memory_store=memory_store,
        event_ledger=event_ledger,
        coalesce_window_ms=settings.ide_coalesce_window_ms,
    )
    state_engine.rebuild_from_ledger()
    ambient_context_service = AmbientContextService(
        state_engine=state_engine,
        memory_store=memory_store,
        policy_engine=policy_engine,
    )
    return ReadOnlyMCPServer(
        ambient_context_service=ambient_context_service,
        state_engine=state_engine,
        event_ledger=event_ledger,
        policy_engine=policy_engine,
    )


def _build_local_context_service(config: Path | None = None) -> AmbientContextService:
    settings = DevCDSettings.load(config)
    policy_engine = PolicyEngine.from_settings(settings)
    memory_store = MemoryStore.with_ttl_seconds(settings.working_memory_ttl_seconds)
    event_ledger = EventLedger(settings.ledger_path)
    state_engine = StateEngine(
        policy_engine=policy_engine,
        memory_store=memory_store,
        event_ledger=event_ledger,
        coalesce_window_ms=settings.ide_coalesce_window_ms,
    )
    state_engine.rebuild_from_ledger()
    return AmbientContextService(
        state_engine=state_engine,
        memory_store=memory_store,
        policy_engine=policy_engine,
        feedback_path=settings.runtime_dir / "context-feedback.jsonl",
    )


def _ensure_mcp_token(settings: DevCDSettings, token: str | None) -> str:
    resolved_token = _resolve_local_mcp_token(settings=settings, token=token)
    if settings.api_token is not None:
        if resolved_token != settings.api_token:
            raise typer.BadParameter("missing or invalid local MCP token")
        return resolved_token

    if resolved_token is not None:
        settings.api_token = resolved_token
        return resolved_token

    generated_token = str(uuid4())
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    token_path = settings.runtime_dir / "token"
    token_path.write_text(generated_token, encoding="utf-8")
    token_path.chmod(0o600)
    settings.api_token = generated_token
    return generated_token


def _resolve_local_mcp_token(settings: DevCDSettings, token: str | None) -> str | None:
    if token:
        return token
    env_token = os.environ.get("DEVCD_TOKEN", "").strip()
    if env_token:
        return env_token

    token_paths = [settings.runtime_dir / "token", _LOCAL_TOKEN_PATH]
    for token_path in token_paths:
        if token_path.exists():
            file_token = token_path.read_text(encoding="utf-8").strip()
            if file_token:
                return file_token
    return None


def _read_jsonl_events(path: Path) -> list[DevEvent]:
    events: list[DevEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(DevEvent.model_validate(json.loads(line)))
        except ValueError as error:
            message = f"invalid JSONL event on line {line_number}: {error}"
            raise typer.BadParameter(message) from error
    return events


def _read_event_file(path: Path) -> DevEvent:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        raise typer.BadParameter(f"{path} is empty")
    if stripped.startswith("{"):
        try:
            return DevEvent.model_validate(json.loads(stripped))
        except ValueError as error:
            raise typer.BadParameter(f"invalid JSON event: {error}") from error

    events = _read_jsonl_events(path)
    if len(events) != 1:
        raise typer.BadParameter("--event JSONL files must contain exactly one event")
    return events[0]


def _explain_ledger_decision(decision_id: str, ledger_path: Path) -> dict[str, Any]:
    policy = PolicyEngine.default()
    for event, decision in EventLedger(ledger_path).read_records():
        if decision.decision_id == decision_id:
            return policy.explain_decision(decision, event).model_dump(mode="json")
    raise typer.BadParameter(f"policy decision not found: {decision_id}")


def _render_policy_simulation(report: dict[str, Any]) -> str:
    lines = [
        f"Policy simulation for surface '{report['surface']}'",
        f"Mutates state: {str(report['mutates_state']).lower()}",
    ]
    for decision in report["decisions"]:
        lines.extend(["", *_render_policy_explanation_lines(decision)])
    return "\n".join(lines)


def _render_policy_explanation(explanation: dict[str, Any]) -> str:
    lines = [f"Policy decision {explanation['decision_id']}"]
    lines.extend(_render_policy_explanation_lines(explanation))
    return "\n".join(lines)


def _render_policy_explanation_lines(explanation: dict[str, Any]) -> list[str]:
    lines = [
        f"Decision: {explanation['kind']} {explanation['operation']}",
        f"Reason: {explanation['reason']}",
        f"Category: {explanation['category']}",
    ]
    source = explanation.get("source")
    data_class = explanation.get("data_class")
    safe_summary = explanation.get("safe_summary")
    if source:
        lines.append(f"Source: {source}")
    if data_class:
        lines.append(f"Data class: {data_class}")
    if safe_summary:
        lines.append(f"Safe replacement: {safe_summary}")
    return lines


def _surface_kind(value: str) -> SurfaceKind:
    try:
        return SurfaceKind(value)
    except ValueError as error:
        raise typer.BadParameter(f"invalid context surface: {value}") from error


def _detail_level(value: str) -> DetailLevel:
    try:
        return DetailLevel(value)
    except ValueError as error:
        raise typer.BadParameter(f"invalid detail level: {value}") from error


def _context_feedback_kind(value: str) -> ContextFeedbackKind:
    try:
        return ContextFeedbackKind(value)
    except ValueError as error:
        allowed = ", ".join(kind.value for kind in ContextFeedbackKind)
        message = f"invalid feedback kind: {value}; expected one of {allowed}"
        raise typer.BadParameter(message) from error


def _render_feedback_result(feedback: ContextFeedback) -> str:
    suffix = " (note withheld by policy)" if feedback.note_withheld else ""
    return f"Stored feedback for {feedback.brief_id}: {feedback.kind.value}{suffix}"


def _render_context_quality(report: ContextQualityReport) -> str:
    lines = ["Context quality feedback", "No ranking or scoring is computed in phase 1.", ""]
    if not report.feedback:
        lines.append("No feedback recorded.")
        return "\n".join(lines)
    for feedback in report.feedback:
        note = feedback.note if feedback.note is not None else "[withheld by policy]"
        lines.append(f"- {feedback.brief_id}: {feedback.kind.value} - {note}")
        lines.append(f"  policy: {feedback.policy_reason}")
    return "\n".join(lines)


def _get_json(endpoint: str, token: str | None = None) -> str:
    headers = {"Accept": "application/json"}
    resolved_token = _resolve_local_api_token(endpoint=endpoint, token=token)
    if resolved_token is not None:
        headers["Authorization"] = f"Bearer {resolved_token}"
    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to fetch context: {error}", err=True)
        raise typer.Exit(1) from error


def _post_json(endpoint: str, body: dict[str, Any], token: str | None = None) -> str:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    resolved_token = _resolve_local_api_token(endpoint=endpoint, token=token)
    if resolved_token is not None:
        headers["Authorization"] = f"Bearer {resolved_token}"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to fetch context: {error}", err=True)
        raise typer.Exit(1) from error


def _patch_json(endpoint: str, body: dict[str, Any], token: str | None = None) -> str:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    resolved_token = _resolve_local_api_token(endpoint=endpoint, token=token)
    if resolved_token is not None:
        headers["Authorization"] = f"Bearer {resolved_token}"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to update context: {error}", err=True)
        raise typer.Exit(1) from error


def _delete_json(endpoint: str, token: str | None = None) -> str:
    headers = {"Accept": "application/json"}
    resolved_token = _resolve_local_api_token(endpoint=endpoint, token=token)
    if resolved_token is not None:
        headers["Authorization"] = f"Bearer {resolved_token}"
    request = urllib.request.Request(endpoint, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to delete context: {error}", err=True)
        raise typer.Exit(1) from error


def _resolve_local_api_token(endpoint: str, token: str | None = None) -> str | None:
    if token:
        return token
    if not _is_loopback_endpoint(endpoint):
        return None

    env_token = os.environ.get("DEVCD_TOKEN", "").strip()
    if env_token:
        return env_token

    if not _LOCAL_TOKEN_PATH.exists():
        return None
    file_token = _LOCAL_TOKEN_PATH.read_text(encoding="utf-8").strip()
    return file_token or None


def _is_loopback_endpoint(endpoint: str) -> bool:
    return urlparse(endpoint).hostname in _LOOPBACK_HOSTS


def main() -> None:
    app()


if __name__ == "__main__":
    main()
