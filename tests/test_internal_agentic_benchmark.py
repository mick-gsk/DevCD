from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devcd.cli import app


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script_path() -> Path:
    return _repo_root() / "scripts" / "internal_agentic_benchmark.py"


def test_internal_benchmark_script_compares_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "devcd.toml"
    config_path.write_text(
        '[devcd]\nruntime_dir = "runtime"\nworking_memory_ttl_seconds = 315360000\n',
        encoding="utf-8",
    )
    runner = CliRunner()

    events = [
        [
            "capture",
            "--kind",
            "attempt",
            "--summary",
            "cold trial failed",
            "--outcome",
            "failed",
            "--session",
            "cold",
            "--config",
            str(config_path),
        ],
        [
            "capture",
            "--kind",
            "attempt",
            "--summary",
            "cold trial succeeded",
            "--outcome",
            "succeeded",
            "--session",
            "cold",
            "--config",
            str(config_path),
        ],
        [
            "capture",
            "--kind",
            "attempt",
            "--summary",
            "devcd trial succeeded",
            "--outcome",
            "succeeded",
            "--session",
            "devcd",
            "--config",
            str(config_path),
        ],
    ]
    for capture_args in events:
        result = runner.invoke(app, capture_args)
        assert result.exit_code == 0

    completed = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--baseline-session",
            "cold",
            "--treatment-session",
            "devcd",
            "--config",
            str(config_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["scope"] == "internal-only"
    assert payload["baseline"]["session"] == "cold"
    assert payload["treatment"]["session"] == "devcd"
    assert payload["comparison"]["failed_attempts_delta"] == -1


def test_internal_benchmark_script_fails_when_session_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "devcd.toml"
    config_path.write_text(
        '[devcd]\nruntime_dir = "runtime"\nworking_memory_ttl_seconds = 315360000\n',
        encoding="utf-8",
    )
    runner = CliRunner()
    capture = runner.invoke(
        app,
        [
            "capture",
            "--kind",
            "attempt",
            "--summary",
            "only cold event",
            "--outcome",
            "succeeded",
            "--session",
            "cold",
            "--config",
            str(config_path),
        ],
    )
    assert capture.exit_code == 0

    completed = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            "--baseline-session",
            "cold",
            "--treatment-session",
            "devcd",
            "--config",
            str(config_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert completed.returncode == 1
    assert "No capture events found for session 'devcd'" in completed.stdout
