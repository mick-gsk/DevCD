from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from devcd.cli import _ensure_mcp_token, _post_event, app
from devcd.kernel.settings import DevCDSettings

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def plain_help(output: str) -> str:
    return ANSI_ESCAPE_RE.sub("", output)


def test_init_writes_default_config(tmp_path) -> None:
    config_path = tmp_path / "devcd.toml"
    runner = CliRunner()

    result = runner.invoke(app, ["init", "--path", str(config_path)])

    assert result.exit_code == 0
    content = config_path.read_text(encoding="utf-8")
    assert "[devcd]" in content
    assert "allow_remote_export = false" in content


def test_cli_exposes_context_group() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "context" in result.output
    assert "mcp" in result.output
    assert "policy" in result.output


def test_cli_exposes_mcp_serve_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["mcp", "serve", "--help"])

    assert result.exit_code == 0
    output = plain_help(result.output)
    assert "Run the local read-only DevCD MCP stdio server" in output
    assert "--config" in output
    assert "--token" in output


def test_mcp_token_gate_creates_local_token_file_when_missing(tmp_path) -> None:
    runtime_dir = tmp_path / "runtime"
    settings = DevCDSettings(runtime_dir=runtime_dir)

    token = _ensure_mcp_token(settings=settings, token=None)

    assert token
    assert settings.api_token == token
    assert (runtime_dir / "token").read_text(encoding="utf-8") == token


def test_mcp_token_gate_rejects_mismatched_configured_token(tmp_path) -> None:
    settings = DevCDSettings(api_token="expected-token", runtime_dir=tmp_path / "runtime")

    with pytest.raises(typer.BadParameter):
        _ensure_mcp_token(settings=settings, token="wrong-token")


def test_cli_exposes_run_alias() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    assert "Run the local DevCD daemon API" in result.output


def test_event_command_accepts_local_api_token() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["event", "--help"])

    assert result.exit_code == 0
    assert "--token" in plain_help(result.output)


def test_post_event_sends_local_api_token(monkeypatch) -> None:
    captured_headers = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self) -> bytes:
            return b'{"kind":"allow"}'

    def fake_urlopen(request: urllib.request.Request, timeout: int):
        captured_headers.update(dict(request.header_items()))
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    response = _post_event(
        endpoint="http://127.0.0.1:8765/event",
        event={"source": "ide", "type": "file_focus", "payload": {}},
        token="local-token",
    )

    assert response == '{"kind":"allow"}'
    assert captured_headers["Authorization"] == "Bearer local-token"


def test_post_event_uses_devcd_token_env_for_loopback(monkeypatch) -> None:
    captured_headers = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self) -> bytes:
            return b'{"kind":"allow"}'

    def fake_urlopen(request: urllib.request.Request, timeout: int):
        captured_headers.update(dict(request.header_items()))
        return FakeResponse()

    monkeypatch.setenv("DEVCD_TOKEN", "env-token")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    _post_event(
        endpoint="http://localhost:8765/event",
        event={"source": "ide", "type": "file_focus", "payload": {}},
    )

    assert captured_headers["Authorization"] == "Bearer env-token"


def test_post_event_uses_local_token_file_for_loopback(monkeypatch, tmp_path) -> None:
    captured_headers = {}
    token_dir = tmp_path / ".devcd"
    token_dir.mkdir()
    (token_dir / "token").write_text("file-token\n", encoding="utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self) -> bytes:
            return b'{"kind":"allow"}'

    def fake_urlopen(request: urllib.request.Request, timeout: int):
        captured_headers.update(dict(request.header_items()))
        return FakeResponse()

    monkeypatch.delenv("DEVCD_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    _post_event(
        endpoint="http://127.0.0.1:8765/event",
        event={"source": "ide", "type": "file_focus", "payload": {}},
    )

    assert captured_headers["Authorization"] == "Bearer file-token"


def test_post_event_does_not_auto_send_local_token_to_remote_endpoint(monkeypatch) -> None:
    captured_headers = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self) -> bytes:
            return b'{"kind":"allow"}'

    def fake_urlopen(request: urllib.request.Request, timeout: int):
        captured_headers.update(dict(request.header_items()))
        return FakeResponse()

    monkeypatch.setenv("DEVCD_TOKEN", "env-token")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    _post_event(
        endpoint="https://example.com/event",
        event={"source": "ide", "type": "file_focus", "payload": {}},
    )

    assert "Authorization" not in captured_headers


def test_cli_exposes_context_brief_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["context", "brief", "--help"])

    assert result.exit_code == 0
    output = plain_help(result.output)
    assert "--surface" in output
    assert "--detail" in output


def test_cli_records_context_feedback_without_echoing_note(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    feedback_result = runner.invoke(
        app,
        [
            "context",
            "feedback",
            "brief-123",
            "--kind",
            "missing",
            "--note",
            "Add the failing test name.",
        ],
    )
    quality_result = runner.invoke(app, ["context", "quality"])

    assert feedback_result.exit_code == 0
    assert "Stored feedback for brief-123" in feedback_result.output
    assert "note withheld" in feedback_result.output
    assert quality_result.exit_code == 0
    assert "brief-123" in quality_result.output
    assert "missing" in quality_result.output
    assert "Add the failing test name." not in quality_result.output
    assert "[withheld by policy]" in quality_result.output
    assert "No ranking or scoring is computed in phase 1." in quality_result.output


def test_cli_withholds_too_sensitive_context_feedback_note(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "context",
            "feedback",
            "brief-123",
            "--kind",
            "too_sensitive",
            "--note",
            "private incident detail",
        ],
    )
    quality_result = runner.invoke(app, ["context", "quality"])

    assert result.exit_code == 0
    assert "note withheld" in result.output
    assert "private incident detail" not in quality_result.output
    assert "[withheld by policy]" in quality_result.output


def test_cli_generates_agent_handoff_demo_brief_from_jsonl(tmp_path) -> None:
    events_path = tmp_path / "sample-events.jsonl"
    events_path.write_text(
        "\n".join(
            [
                (
                    '{"source":"task","type":"goal_update",'
                    '"payload":{"current_goal":"Ship Agent-Handoff MVP"}}'
                ),
                (
                    '{"source":"ide","type":"file_focus",'
                    '"payload":{"path":"packages/devcd-core/src/devcd/slices/'
                    'ambient_context/service.py","duration_seconds":120}}'
                ),
                '{"source":"git","type":"branch_change","payload":{"branch":"main"}}',
                '{"source":"task","type":"test_failure","payload":{"reason":"make check failed"}}',
                (
                    '{"source":"browser","type":"url_focus",'
                    '"payload":{"url":"https://internal.invalid/private-ticket"}}'
                ),
            ]
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["context", "handoff-demo", "--events", str(events_path)])

    assert result.exit_code == 0
    assert "# DevCD Agent Handoff Brief" in result.output
    assert "active_goal" in result.output
    assert "Ship Agent-Handoff MVP" in result.output
    assert "git_context" in result.output
    assert "blockers" in result.output
    assert "withheld_context" in result.output
    assert "agent_limitations" in result.output
    assert "cannot see" in result.output
    assert "source is not enabled by policy" in result.output
    assert "browser url_focus signal was withheld" in result.output


def test_cli_handoff_demo_sample_events_remain_actionable() -> None:
    runner = CliRunner()
    events_path = Path("examples/agent-handoff/sample-events.jsonl")

    result = runner.invoke(app, ["context", "handoff-demo", "--events", str(events_path)])

    assert result.exit_code == 0
    assert "## brief_id" in result.output
    assert "Ship Agent-Handoff MVP for DevCD" in result.output
    assert "packages/devcd-core/src/devcd/slices/ambient_context/service.py" in result.output
    assert "- branch: main" in result.output
    assert "- latest_commit: abc1234" in result.output
    assert "No active goal available" not in result.output
    assert "latest_commit: unknown" not in result.output


def test_cli_exposes_dismiss_suggestion_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["context", "dismiss-suggestion", "--help"])

    assert result.exit_code == 0
    assert "suggestion-id" in result.output


def test_cli_exposes_context_memory_commands() -> None:
    runner = CliRunner()

    memory = runner.invoke(app, ["context", "memory", "--help"])
    correct = runner.invoke(app, ["context", "memory-correct", "--help"])
    delete = runner.invoke(app, ["context", "memory-delete", "--help"])

    assert memory.exit_code == 0
    assert "--scope" in plain_help(memory.output)
    assert correct.exit_code == 0
    assert "item-id" in correct.output
    assert delete.exit_code == 0
    assert "item-id" in delete.output


def test_policy_simulate_outputs_json_and_human_explanation(tmp_path) -> None:
    events_path = tmp_path / "sensitive-event.json"
    events_path.write_text(
        json.dumps(
            {
                "source": "notes",
                "type": "note_update",
                "payload": {"title": "Private credentials note"},
                "sensitivity": "sensitive",
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    json_result = runner.invoke(
        app,
        ["policy", "simulate", "--surface", "coding-agent", "--event", str(events_path), "--json"],
    )
    human_result = runner.invoke(
        app,
        ["policy", "simulate", "--surface", "coding-agent", "--event", str(events_path)],
    )

    assert json_result.exit_code == 0
    body = json.loads(json_result.output)
    assert body["mutates_state"] is False
    assert body["decisions"][0]["kind"] == "deny"
    assert body["decisions"][0]["category"] == "sensitivity"
    assert "sensitive events" in body["decisions"][0]["reason"]
    assert "Private credentials note" not in body["decisions"][0]["safe_summary"]
    assert "notes note_update signal was withheld" in body["withheld"][0]["safe_summary"]

    assert human_result.exit_code == 0
    assert "Policy simulation for surface 'coding-agent'" in human_result.output
    assert "Decision: deny observe" in human_result.output
    assert "Category: sensitivity" in human_result.output
    assert "Safe replacement:" in human_result.output
    assert "Private credentials note" not in human_result.output


def test_policy_simulate_does_not_write_local_ledger(tmp_path, monkeypatch) -> None:
    events_path = tmp_path / "sensitive-event.json"
    events_path.write_text(
        json.dumps(
            {
                "source": "notes",
                "type": "note_update",
                "payload": {"title": "Private credentials note"},
                "sensitivity": "sensitive",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["policy", "simulate", "--surface", "coding-agent", "--event", str(events_path)],
    )

    assert result.exit_code == 0
    assert not (tmp_path / ".devcd" / "events.jsonl").exists()


def test_policy_explain_reads_decision_from_ledger_as_json_and_text(tmp_path) -> None:
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text(
        json.dumps(
            {
                "event": {
                    "event_id": "event-sensitive-1",
                    "source": "notes",
                    "type": "note_update",
                    "payload": {"title": "Private credentials note"},
                    "sensitivity": "sensitive",
                    "data_class": "metadata",
                },
                "policy_decision": {
                    "decision_id": "decision-sensitive-1",
                    "kind": "deny",
                    "reason": "sensitive events are denied by the default local policy",
                    "operation": "observe",
                    "source": "notes",
                    "data_class": "metadata",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = CliRunner()

    json_result = runner.invoke(
        app,
        [
            "policy",
            "explain",
            "decision-sensitive-1",
            "--ledger",
            str(ledger_path),
            "--json",
        ],
    )
    human_result = runner.invoke(
        app,
        ["policy", "explain", "decision-sensitive-1", "--ledger", str(ledger_path)],
    )

    assert json_result.exit_code == 0
    body = json.loads(json_result.output)
    assert body["decision_id"] == "decision-sensitive-1"
    assert body["allowed"] is False
    assert body["category"] == "sensitivity"
    assert "sensitive events" in body["reason"]
    assert "Private credentials note" not in body["safe_summary"]

    assert human_result.exit_code == 0
    assert "Policy decision decision-sensitive-1" in human_result.output
    assert "Decision: deny observe" in human_result.output
    assert "Category: sensitivity" in human_result.output
    assert "Safe replacement:" in human_result.output
