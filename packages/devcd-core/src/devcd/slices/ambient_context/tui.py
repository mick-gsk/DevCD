"""Interactive Textual TUI for the DevCD quickstart onboarding experience."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Collapsible, Footer, Header, Label, Log, Markdown, Static

# ── Command allowlist ─────────────────────────────────────────────────────────
# Only these exact argv tuples may be executed by the TUI.
# No shell=True, no string concatenation, no user input in args.
ALLOWED_QUICKSTART_COMMANDS: frozenset[tuple[str, ...]] = frozenset(
    {
        ("devcd", "init"),
        ("devcd", "status"),
        ("devcd", "doctor"),
        ("devcd", "context", "passport"),
        ("devcd", "integrations", "openclaw", "--smoke-test"),
    }
)

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """\
Screen { background: $surface; }

.h-layout { height: 1fr; }

#sidebar {
    width: 30;
    background: $panel;
    border-right: vkey $primary-darken-2;
    padding: 1 2;
}

.state-title { text-style: bold; color: $accent; margin-bottom: 1; }
.state-ok    { color: $success; }
.state-warn  { color: $warning; }
.state-neutral { color: $text-muted; }

#content { padding: 1 3; }

.value-prop {
    border: round $accent-darken-2;
    padding: 1 2;
    margin-bottom: 2;
    color: $text-muted;
}

.path-btn { width: 100%; height: 4; margin-bottom: 1; }

Collapsible { margin-bottom: 1; }

.cmd-block {
    background: $boost;
    color: $success;
    padding: 0 2;
    margin: 1 0;
}

.step-prose { color: $text-muted; margin: 0 0 1 0; }
.run-btn { margin-top: 1; }

Log { height: 8; margin-top: 1; border: solid $surface-lighten-1; }

.log-hidden { display: none; }

.next-hint {
    background: $success-darken-3;
    border: solid $success;
    padding: 1 2;
    margin-top: 2;
}

.section-header { text-style: bold; color: $accent; margin: 1 0; }
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _devcd_exe() -> str | None:
    """Locate the devcd binary on PATH."""
    return shutil.which("devcd")


async def _exec_allowed(argv: tuple[str, ...], log: Log) -> int:
    """Execute an allowlisted devcd command, streaming stdout/stderr to *log*."""
    if argv not in ALLOWED_QUICKSTART_COMMANDS:
        log.write_line("Error: command not in allowed list")
        return 1
    exe = _devcd_exe()
    if exe is None:
        log.write_line("Error: devcd not found on PATH")
        return 1
    proc = await asyncio.create_subprocess_exec(
        exe,
        *argv[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    if proc.stdout is not None:
        async for raw in proc.stdout:
            log.write_line(raw.decode(errors="replace").rstrip())
    await proc.wait()
    return proc.returncode or 0


def _sidebar(local_state: dict[str, Any]) -> Vertical:
    """Build the persistent local-state sidebar widget."""
    config_ok = bool(local_state.get("config_exists", False))
    daemon_ok = bool(local_state.get("daemon_reachable", False))
    events_count = int(local_state.get("events_count", 0))
    goal: str | None = local_state.get("active_goal")
    token = str(local_state.get("token_source", "missing"))

    def row(text: str, css: str = "neutral") -> Label:
        return Label(text, classes=f"state-{css}")

    return Vertical(
        row("Local State", "title"),
        row(f"  Config   {'✓' if config_ok else '✗'}", "ok" if config_ok else "warn"),
        row(f"  Daemon   {'✓' if daemon_ok else '✗'}", "ok" if daemon_ok else "warn"),
        row(f"  Token    {token[:18]}", "ok" if token != "missing" else "warn"),
        row(f"  Events   {events_count}", "ok" if events_count > 0 else "neutral"),
        row(f"  Goal     {(goal or '—')[:20]}", "ok" if goal else "neutral"),
        id="sidebar",
    )


# ── Screens ───────────────────────────────────────────────────────────────────


class DemoScreen(Screen[None]):  # type: ignore[type-arg]
    """Renders the demo Agent Passport with an explanation panel."""

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        demo = self._report["demo_first"]
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(self._report["local_state"])
            with ScrollableContainer(id="content"):
                yield Markdown(str(demo["packet_markdown"]))
                yield Static(
                    "What you see:\n"
                    "  Goal           — what the previous agent was working toward\n"
                    "  Latest failure — what broke last\n"
                    "  Do-not-repeat  — tested fixes that did not work\n"
                    "  Withheld       — sensitive data held back by local policy\n",
                    markup=False,
                    classes="value-prop",
                )
                yield Label(
                    "Next step:  devcd init  →  devcd run  →  devcd context passport",
                    classes="next-hint",
                )
        yield Footer()


class LiveSetupScreen(Screen[None]):  # type: ignore[type-arg]
    """Step-by-step live daemon setup with optional command execution."""

    BINDINGS = [Binding("escape", "back", "Back")]

    _LIVE_STEP_IDS: tuple[str, ...] = ("init", "readiness", "daemon", "first_event", "passport")

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report
        self._steps = [s for s in report["steps"] if s["id"] in self._LIVE_STEP_IDS]

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(self._report["local_state"])
            with ScrollableContainer(id="content"):
                yield Label("Live Setup — step by step", classes="section-header")
                for step in self._steps:
                    argv = tuple(step["command"].split())
                    can_run = argv in ALLOWED_QUICKSTART_COMMANDS
                    # Auto-expand the first step that hasn't been completed yet
                    already_done = step["status"] in {
                        "present",
                        "reachable",
                        "already has events",
                        "ready",
                    }
                    with Collapsible(title=f"  {step['title']}", collapsed=already_done):
                        yield Label(step["what_happened"], classes="step-prose")
                        yield Static(
                            f"  $ {step['command']}",
                            markup=False,
                            classes="cmd-block",
                        )
                        yield Label(f"Success: {step['success_looks_like']}", classes="step-prose")
                        if can_run:
                            yield Button(
                                "▶  Run now",
                                variant="success",
                                id=f"run-{step['id']}",
                                classes="run-btn",
                            )
                            yield Log(
                                id=f"log-{step['id']}",
                                highlight=False,
                                classes="log-hidden",
                            )
                        else:
                            yield Label(
                                "Run this in a separate terminal window.",
                                classes="step-prose",
                            )
        yield Footer()

    @on(Button.Pressed)
    def _on_run_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("run-"):
            self._execute_step(btn_id[4:])

    @work(exclusive=False)
    async def _execute_step(self, step_id: str) -> None:
        btn = self.query_one(f"#run-{step_id}", Button)
        log = self.query_one(f"#log-{step_id}", Log)
        btn.disabled = True
        log.remove_class("log-hidden")
        step = next((s for s in self._steps if s["id"] == step_id), None)
        if step is None:
            return
        argv = tuple(step["command"].split())
        rc = await _exec_allowed(argv, log)
        if rc == 0:
            btn.label = "✓  Done"
            btn.variant = "default"
        else:
            btn.label = "✗  Failed — see output above"
            btn.variant = "error"
            btn.disabled = False


class McpScreen(Screen[None]):  # type: ignore[type-arg]
    """MCP integration path — smoke test and config snippet."""

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(self._report["local_state"])
            with ScrollableContainer(id="content"):
                yield Label("MCP Integration", classes="section-header")
                yield Label(
                    "Connect DevCD as a read-only MCP context server for OpenClaw or Hermes.",
                    classes="step-prose",
                )
                with Collapsible(title="  Step 1: Verify MCP smoke test", collapsed=False):
                    yield Label(
                        "Verifies that the MCP server starts, lists resources, and "
                        "responds correctly — no OpenClaw installation required.",
                        classes="step-prose",
                    )
                    yield Static(
                        "  $ devcd integrations openclaw --smoke-test",
                        markup=False,
                        classes="cmd-block",
                    )
                    yield Button(
                        "▶  Run smoke test",
                        variant="success",
                        id="run-mcp-smoke",
                        classes="run-btn",
                    )
                    yield Log(id="log-mcp-smoke", highlight=False, classes="log-hidden")
                with Collapsible(title="  Step 2: Add MCP config to OpenClaw", collapsed=True):
                    yield Label(
                        "Copy this snippet into your OpenClaw configuration:",
                        classes="step-prose",
                    )
                    yield Static(
                        "  {\n"
                        '    "mcp": {\n'
                        '      "servers": {\n'
                        '        "devcd": {\n'
                        '          "command": "devcd",\n'
                        '          "args": ["mcp", "serve"]\n'
                        "        }\n"
                        "      }\n"
                        "    }\n"
                        "  }",
                        markup=False,
                        classes="cmd-block",
                    )
        yield Footer()

    @on(Button.Pressed, "#run-mcp-smoke")
    def _on_smoke_pressed(self, event: Button.Pressed) -> None:
        self._run_smoke_test()

    @work(exclusive=True)
    async def _run_smoke_test(self) -> None:
        btn = self.query_one("#run-mcp-smoke", Button)
        log = self.query_one("#log-mcp-smoke", Log)
        btn.disabled = True
        log.remove_class("log-hidden")
        rc = await _exec_allowed(("devcd", "integrations", "openclaw", "--smoke-test"), log)
        if rc == 0:
            btn.label = "✓  Passed"
            btn.variant = "default"
        else:
            btn.label = "✗  Failed — see output above"
            btn.variant = "error"
            btn.disabled = False


# ── Main App ──────────────────────────────────────────────────────────────────


class QuickstartApp(App[None]):  # type: ignore[type-arg]
    """DevCD interactive quickstart TUI."""

    TITLE = "DevCD Quickstart"
    CSS = _CSS
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report

    async def action_quit(self) -> None:
        self.exit()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(self._report["local_state"])
            with ScrollableContainer(id="content"):
                yield Static(
                    self._report["value_proposition"],
                    classes="value-prop",
                    markup=False,
                )
                yield Label("Choose a path to get started:", classes="section-header")
                yield Button(
                    "  [D]  Demo Passport\n  See continuity in 2 minutes — no daemon required",
                    id="path-demo",
                    classes="path-btn",
                    variant="primary",
                )
                yield Button(
                    "  [L]  Live Setup\n  Configure daemon, send events, get a live passport",
                    id="path-live",
                    classes="path-btn",
                    variant="default",
                )
                yield Button(
                    "  [M]  MCP Integration\n  Connect OpenClaw or Hermes as a context consumer",
                    id="path-mcp",
                    classes="path-btn",
                    variant="default",
                )
        yield Footer()

    @on(Button.Pressed, "#path-demo")
    def _open_demo(self, event: Button.Pressed) -> None:
        self.push_screen(DemoScreen(self._report))

    @on(Button.Pressed, "#path-live")
    def _open_live(self, event: Button.Pressed) -> None:
        self.push_screen(LiveSetupScreen(self._report))

    @on(Button.Pressed, "#path-mcp")
    def _open_mcp(self, event: Button.Pressed) -> None:
        self.push_screen(McpScreen(self._report))
