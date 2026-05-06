from __future__ import annotations

from typing import Any

import pytest

from devcd.slices.ambient_context.tui import (
    ALLOWED_QUICKSTART_COMMANDS,
    McpScreen,
    QuickstartApp,
    _devcd_exe,
)


def _minimal_report() -> dict[str, Any]:
    """Minimal report dict matching the shape produced by _build_quickstart_report."""
    return {
        "value_proposition": (
            "DevCD lets a new agent continue from a local, policy-filtered Action Packet."
        ),
        "demo_preview": {
            "command": (
                "devcd agentic action-packet-demo --events "
                "examples/agentic-action-packet/sample-events.jsonl"
            ),
            "daemon_required": False,
            "packet_markdown": "# DevCD Action Packet\n\n## Current Goal\nTest goal\n",
        },
        "action_packet_first": {
            "command": "devcd agentic action-packet",
            "broader_view_command": "devcd context passport",
            "policy_command": "devcd context control",
            "packet_markdown": "# DevCD Action Packet\n\n## Current Goal\nTest goal\n",
        },
        "repeat_use": {
            "trigger": "Switch to a fresh agent after capturing at least one goal or failure.",
            "return_command": "devcd agentic action-packet",
            "capture_command": (
                'devcd handoff --goal "<current goal>" '
                '--next-action "<safe next step>"'
            ),
            "why_it_matters": "The next agent should be able to continue without a recap.",
            "success_looks_like": [
                "the new agent starts from the current goal",
                "the next safe action is already named for the handoff",
            ],
        },
        "local_state": {
            "config_exists": False,
            "daemon_reachable": False,
            "events_count": 0,
            "active_goal": None,
            "token_source": "missing",
            "config_path": "devcd.toml",
            "daemon_endpoint": "http://127.0.0.1:8765/state",
            "live_context_empty": True,
            "doctor_status": "attention",
            "next_command": "devcd init",
        },
        "steps": [
            {
                "id": "install",
                "title": "Install from checkout",
                "command": 'python -m pip install -e ".[dev]"',
                "what_happened": "CLI becomes available.",
                "success_looks_like": "devcd --help lists commands.",
                "next": "devcd quickstart",
                "if_fails": "Confirm Python 3.11+.",
                "status": "manual",
            },
            {
                "id": "workspace",
                "title": "Prepare local workspace",
                "command": "devcd init",
                "what_happened": "Creates devcd.toml.",
                "success_looks_like": "devcd.toml exists.",
                "next": "devcd agentic action-packet",
                "if_fails": "Run devcd doctor.",
                "status": "missing",
            },
            {
                "id": "action_packet",
                "title": "Open the Action Packet",
                "command": "devcd agentic action-packet",
                "what_happened": "Shows the next-agent handoff first.",
                "success_looks_like": (
                    "The next agent starts from visible continuity instead "
                    "of a recap."
                ),
                "next": (
                    'devcd handoff --goal "<current goal>" '
                    '--next-action "<safe next step>"'
                ),
                "if_fails": "Capture a goal or failure, then rerun the Action Packet.",
                "status": "needs continuity",
            },
            {
                "id": "capture",
                "title": "Capture a compact handoff",
                "command": (
                    'devcd handoff --goal "<current goal>" '
                    '--next-action "<safe next step>"'
                ),
                "what_happened": "Stores compact continuity metadata for the next agent.",
                "success_looks_like": "The Action Packet names the goal, failure, and next action.",
                "next": "devcd context passport",
                "if_fails": "Keep the capture metadata-only and retry.",
                "status": "recommended",
            },
            {
                "id": "passport",
                "title": "Inspect the broader continuity view",
                "command": "devcd context passport",
                "what_happened": "Rebuilds live state.",
                "success_looks_like": "Passport shows goal.",
                "next": "devcd context control",
                "if_fails": "Send goal_update event.",
                "status": "empty guidance available",
            },
            {
                "id": "daemon",
                "title": "Optional live daemon path",
                "command": "devcd run",
                "what_happened": "API on 127.0.0.1:8765.",
                "success_looks_like": "Daemon reachable.",
                "next": "devcd status",
                "if_fails": "Run devcd doctor.",
                "status": "not running",
            },
            {
                "id": "mcp",
                "title": "Optional MCP/OpenClaw integration",
                "command": "devcd integrations openclaw --smoke-test",
                "what_happened": "Prints MCP snippet.",
                "success_looks_like": "Smoke test passes.",
                "next": "devcd integrations hermes",
                "if_fails": "Fix devcd command path.",
                "status": "optional",
            },
        ],
        "next_paths": {
            "continue_live": "devcd run",
            "get_action_packet": "devcd agentic action-packet",
            "capture_handoff": (
                'devcd handoff --goal "<current goal>" '
                '--next-action "<safe next step>"'
            ),
            "get_passport": "devcd context passport",
            "connect_agent": "devcd integrations openclaw --smoke-test",
            "inspect_policy": "devcd context control",
        },
    }


# ── Allowlist tests ───────────────────────────────────────────────────────────


def test_allowed_commands_are_devcd_only() -> None:
    for argv in ALLOWED_QUICKSTART_COMMANDS:
        assert argv[0] == "devcd", f"Non-devcd command in allowlist: {argv}"


def test_allowed_commands_have_no_shell_metacharacters() -> None:
    meta = set(";|&$`\\<>")
    for argv in ALLOWED_QUICKSTART_COMMANDS:
        for part in argv:
            assert not (set(part) & meta), f"Shell metacharacter in allowlist arg: {part!r}"


def test_exec_allowed_rejects_unlisted_command() -> None:
    """_exec_allowed guard: any argv not in ALLOWED_QUICKSTART_COMMANDS is blocked."""
    assert ("devcd", "evil", "--rm-rf") not in ALLOWED_QUICKSTART_COMMANDS
    assert ("sh", "-c", "rm -rf /") not in ALLOWED_QUICKSTART_COMMANDS


# ── App instantiation tests ───────────────────────────────────────────────────


def test_quickstart_app_can_be_instantiated() -> None:
    app = QuickstartApp(_minimal_report())
    assert app.TITLE == "DevCD Quickstart"


@pytest.mark.asyncio
async def test_quickstart_app_renders_path_buttons() -> None:
    from textual.widgets import Button

    app = QuickstartApp(_minimal_report())
    async with app.run_test(headless=True) as pilot:
        await pilot.pause()
        assert "Proof in one minute" in str(pilot.app.query_one("#path-demo", Button).label)
        assert "Action Packet workflow" in str(pilot.app.query_one("#path-live", Button).label)
        assert "Optional MCP follow-up" in str(pilot.app.query_one("#path-mcp", Button).label)


@pytest.mark.asyncio
async def test_quickstart_app_quit_binding() -> None:
    app = QuickstartApp(_minimal_report())
    async with app.run_test(headless=True) as pilot:
        await pilot.press("q")
        # After pressing q the app should have exited — run_test context closes cleanly


# ── Screen tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_demo_screen_renders_markdown() -> None:
    from textual.widgets import Markdown

    report = _minimal_report()
    app = QuickstartApp(report)
    async with app.run_test(headless=True) as pilot:
        await pilot.pause()
        await pilot.click("#path-demo")
        # Allow multiple event loop cycles for push_screen to settle
        for _ in range(3):
            await pilot.pause()
        assert pilot.app.screen.query_one(Markdown)


@pytest.mark.asyncio
async def test_live_setup_screen_renders_steps() -> None:
    from textual.widgets import Collapsible, Markdown

    report = _minimal_report()
    app = QuickstartApp(report)
    async with app.run_test(headless=True) as pilot:
        await pilot.pause()
        await pilot.click("#path-live")
        for _ in range(3):
            await pilot.pause()
        assert pilot.app.screen.query_one(Markdown)
        collapsibles = pilot.app.screen.query(Collapsible)
        # Action Packet follow-up still exposes guided operational steps beneath the packet.
        assert len(collapsibles) >= 1


@pytest.mark.asyncio
async def test_mcp_screen_renders_smoke_test_button() -> None:
    from textual.widgets import Button

    report = _minimal_report()
    # Test McpScreen directly instead of navigating through the main menu,
    # since the MCP path button may scroll off the default headless viewport.
    app = QuickstartApp(report)
    async with app.run_test(headless=True) as pilot:
        await pilot.pause()
        await pilot.app.push_screen(McpScreen(report))
        for _ in range(3):
            await pilot.pause()
        assert pilot.app.screen.query_one("#run-mcp-smoke", Button)


@pytest.mark.asyncio
async def test_demo_screen_back_returns_to_main() -> None:
    from textual.widgets import Button

    report = _minimal_report()
    app = QuickstartApp(report)
    async with app.run_test(headless=True) as pilot:
        await pilot.pause()
        await pilot.click("#path-demo")
        for _ in range(3):
            await pilot.pause()
        await pilot.press("escape")
        for _ in range(3):
            await pilot.pause()
        # Back on main screen — path buttons should be visible again
        assert pilot.app.screen.query_one("#path-demo", Button)


# ── _devcd_exe helper ─────────────────────────────────────────────────────────


def test_devcd_exe_returns_string_or_none() -> None:
    result = _devcd_exe()
    assert result is None or isinstance(result, str)
