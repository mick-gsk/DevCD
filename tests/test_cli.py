from __future__ import annotations

from typer.testing import CliRunner

from devcd.cli import app


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


def test_cli_exposes_context_brief_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["context", "brief", "--help"])

    assert result.exit_code == 0
    assert "--surface" in result.output
    assert "--detail" in result.output


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
    assert "--scope" in memory.output
    assert correct.exit_code == 0
    assert "item-id" in correct.output
    assert delete.exit_code == 0
    assert "item-id" in delete.output
