from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Annotated

import tomli_w
import typer
import uvicorn

from devcd.kernel.settings import DevCDSettings
from devcd.host import create_app

app = typer.Typer(help="DevCD local context daemon.")


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
    sensitivity: Annotated[str, typer.Option("--sensitivity", help="normal or sensitive.")] = "normal",
) -> None:
    """Submit a normalized event to a running daemon."""
    parsed_payload = json.loads(payload)
    if not isinstance(parsed_payload, dict):
        raise typer.BadParameter("--payload must be a JSON object")

    body = json.dumps(
        {
            "source": source,
            "type": event_type,
            "payload": parsed_payload,
            "sensitivity": sensitivity,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            typer.echo(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        typer.echo(f"Failed to submit event: {error}", err=True)
        raise typer.Exit(1) from error


def main() -> None:
    app()


if __name__ == "__main__":
    main()
