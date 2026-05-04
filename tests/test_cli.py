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
