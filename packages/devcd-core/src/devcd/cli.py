from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Annotated, Any, cast
from urllib.parse import quote

import tomli_w
import typer
import uvicorn

from devcd.host import create_app
from devcd.kernel.settings import DevCDSettings
from devcd.slices.git_source.service import GitEventSource

app = typer.Typer(help="DevCD local context daemon.")
context_app = typer.Typer(help="Inspect ambient developer context.")
app.add_typer(context_app, name="context")


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
    )
    typer.echo(response)


@app.command("git-snapshot")
def git_snapshot(
    repo: Annotated[Path, typer.Option("--repo", help="Git repository to inspect.")] = Path("."),
    endpoint: Annotated[
        str, typer.Option("--endpoint", help="DevCD daemon endpoint.")
    ] = "http://127.0.0.1:8765/event",
) -> None:
    """Submit branch and latest-commit events for a Git repository."""
    events = GitEventSource().collect_snapshot_events(repo)
    if not events:
        typer.echo("No git events collected")
        return

    for git_event in events:
        typer.echo(_post_event(endpoint=endpoint, event=git_event.model_dump(mode="json")))


@context_app.callback()
def context() -> None:
    """Ambient context commands."""


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


def _post_event(endpoint: str, event: dict[str, Any]) -> str:
    body = json.dumps(event).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to submit event: {error}", err=True)
        raise typer.Exit(1) from error


def _get_json(endpoint: str, token: str | None = None) -> str:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to fetch context: {error}", err=True)
        raise typer.Exit(1) from error


def _post_json(endpoint: str, body: dict[str, Any], token: str | None = None) -> str:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
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
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
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
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(endpoint, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return cast(str, response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to delete context: {error}", err=True)
        raise typer.Exit(1) from error


def main() -> None:
    app()


if __name__ == "__main__":
    main()
