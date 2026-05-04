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
from devcd.slices.ambient_context.models import AgentContextSurface, DetailLevel, SurfaceKind
from devcd.slices.ambient_context.service import (
    AmbientContextService,
    render_context_brief_markdown,
)
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent
from devcd.slices.git_source.service import GitEventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.mcp_server.service import ReadOnlyMCPServer, serve_stdio
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine

app = typer.Typer(help="DevCD local context daemon.")
context_app = typer.Typer(help="Inspect ambient developer context.")
mcp_app = typer.Typer(help="Serve read-only DevCD context through MCP.")
policy_app = typer.Typer(help="Explain and simulate local policy decisions.")
app.add_typer(context_app, name="context")
app.add_typer(mcp_app, name="mcp")
app.add_typer(policy_app, name="policy")

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


@context_app.command("handoff-demo")
def context_handoff_demo(
    events: Annotated[Path, typer.Option("--events", help="JSONL file with DevCD events.")],
    surface: Annotated[str, typer.Option("--surface", help="Context surface kind.")] = "cli",
    detail: Annotated[
        str, typer.Option("--detail", help="minimal, standard, or diagnostic.")
    ] = "standard",
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
    memory_store = MemoryStore.with_default_ttl()
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
