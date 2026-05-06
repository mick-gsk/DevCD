"""Interactive Textual TUI for the DevCD quickstart onboarding experience."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any, cast

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
        ("devcd", "agentic", "action-packet"),
        ("devcd", "context", "passport"),
        ("devcd", "context", "control"),
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

.agent-layer {
    border: round $primary-darken-1;
    padding: 1 2;
    margin-bottom: 1;
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


def _sidebar(local_state: dict[str, Any], agent_layer: dict[str, Any] | None = None) -> Vertical:
    """Build the persistent local-state sidebar widget."""
    config_ok = bool(local_state.get("config_exists", False))
    daemon_ok = bool(local_state.get("daemon_reachable", False))
    events_count = int(local_state.get("events_count", 0))
    goal: str | None = local_state.get("active_goal")
    token = str(local_state.get("token_source", "missing"))
    profile_status = str((agent_layer or {}).get("profile_status", "unknown"))
    archetype = str((agent_layer or {}).get("archetype", "auto"))

    def row(text: str, css: str = "neutral") -> Label:
        return Label(text, classes=f"state-{css}")

    return Vertical(
        row("Local State", "title"),
        row(f"  Config   {'✓' if config_ok else '✗'}", "ok" if config_ok else "warn"),
        row(f"  Daemon   {'✓' if daemon_ok else '✗'}", "ok" if daemon_ok else "warn"),
        row(f"  Token    {token[:18]}", "ok" if token != "missing" else "warn"),
        row(f"  Events   {events_count}", "ok" if events_count > 0 else "neutral"),
        row(f"  Goal     {(goal or '—')[:20]}", "ok" if goal else "neutral"),
        row("Agent Layer", "title"),
        row(f"  Profile  {profile_status[:18]}", "ok" if profile_status == "ready" else "warn"),
        row(f"  Layer    {archetype[:18]}", "neutral"),
        id="sidebar",
    )


def _agent_layer_panel(report: dict[str, Any]) -> Vertical:
    agent_layer = cast(dict[str, Any], report.get("agent_layer") or {})
    targets = ", ".join(cast(list[str], agent_layer.get("agent_targets", []))) or "none"
    surfaces = ", ".join(cast(list[str], agent_layer.get("surface_plan", [])))
    tools = ", ".join(cast(list[str], agent_layer.get("detected_tools", []))) or "none"
    progress = " -> ".join(
        str(item["label"]) for item in cast(list[dict[str, Any]], agent_layer.get("progress", []))
    )
    summary = (
        f"Agent layer: {agent_layer.get('archetype', 'auto')}\n"
        f"Profile: {agent_layer.get('profile_status', 'unknown')}\n"
        f"Context pack: {agent_layer.get('context_pack', 'developer')}\n"
        f"Agents: {targets}\n"
        f"Surfaces: {surfaces}\n"
        f"Detected tools: {tools}\n"
        f"Next: {agent_layer.get('next_action', 'devcd onboard --yes')}"
    )
    return Vertical(
        Label("Agent Layer", classes="section-header"),
        Static(summary, id="agent-layer-summary", markup=False, classes="agent-layer"),
        Static(progress, id="agent-layer-progress", markup=False, classes="step-prose"),
    )


# ── Screens ───────────────────────────────────────────────────────────────────


class DemoScreen(Screen[None]):  # type: ignore[type-arg]
    """Renders the fastest proof path for the Action Packet workflow."""

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        demo = cast(dict[str, Any], self._report.get("demo_preview") or {})
        command = str(
            demo.get(
                "command",
                "devcd agentic action-packet-demo --events "
                "examples/agentic-action-packet/sample-events.jsonl",
            )
        )
        packet_markdown = str(
            demo.get(
                "packet_markdown",
                (
                    "# Proof in one minute\n\n"
                    "Run the checked-in Action Packet demo to preview the "
                    "warm-start handoff without touching your workspace."
                ),
            )
        )
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(
                self._report["local_state"],
                cast(dict[str, Any], self._report.get("agent_layer")),
            )
            with ScrollableContainer(id="content"):
                yield Label("Proof in one minute", classes="section-header")
                yield Static(f"  $ {command}", markup=False, classes="cmd-block")
                yield Markdown(packet_markdown)
                yield Static(
                    (
                        "What you prove:\n"
                        "  Action Packet  — the next agent gets a compact handoff first\n"
                        "  Policy notes    — withheld context stays visible "
                        "without leaking raw payloads\n"
                        "  No daemon       — the proof works without live "
                        "ingestion or external mutation\n"
                    ),
                    markup=False,
                    classes="value-prop",
                )
                yield Label(
                    (
                        "Next step:  devcd onboard  ->  devcd agentic "
                        "action-packet  ->  devcd quickstart"
                    ),
                    classes="next-hint",
                )
        yield Footer()


class LiveSetupScreen(Screen[None]):  # type: ignore[type-arg]
    """Interactive follow-up for the Action Packet workflow."""

    BINDINGS = [Binding("escape", "back", "Back")]

    _LIVE_STEP_IDS: tuple[str, ...] = (
        "workspace",
        "action_packet",
        "capture",
        "passport",
        "daemon",
    )

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__()
        self._report = report
        self._steps = [s for s in report["steps"] if s["id"] in self._LIVE_STEP_IDS]

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        action_packet_first = cast(dict[str, Any], self._report["action_packet_first"])
        repeat_use = cast(dict[str, Any], self._report["repeat_use"])
        yield Header(show_clock=False)
        with Horizontal(classes="h-layout"):
            yield _sidebar(
                self._report["local_state"],
                cast(dict[str, Any], self._report.get("agent_layer")),
            )
            with ScrollableContainer(id="content"):
                yield Label("Action Packet workflow", classes="section-header")
                yield Static(
                    self._report["value_proposition"],
                    classes="value-prop",
                    markup=False,
                )
                yield Markdown(str(action_packet_first["packet_markdown"]))
                yield Label(
                    f"Come back with: {repeat_use['return_command']}",
                    classes="next-hint",
                )
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
            yield _sidebar(
                self._report["local_state"],
                cast(dict[str, Any], self._report.get("agent_layer")),
            )
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
            yield _sidebar(
                self._report["local_state"],
                cast(dict[str, Any], self._report.get("agent_layer")),
            )
            with ScrollableContainer(id="content"):
                yield Static(
                    self._report["value_proposition"],
                    classes="value-prop",
                    markup=False,
                )
                yield _agent_layer_panel(self._report)
                yield Label("Choose your next move:", classes="section-header")
                yield Button(
                    (
                        "  [D]  Proof in one minute\n"
                        "  Preview the checked-in Action Packet before "
                        "touching your workspace"
                    ),
                    id="path-demo",
                    classes="path-btn",
                    variant="primary",
                )
                yield Button(
                    (
                        "  [L]  Action Packet workflow\n"
                        "  Follow the real workspace path around onboard "
                        "and quickstart"
                    ),
                    id="path-live",
                    classes="path-btn",
                    variant="default",
                )
                yield Button(
                    (
                        "  [M]  Optional MCP follow-up\n"
                        "  Connect a read-only context consumer after the "
                        "primary flow"
                    ),
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
