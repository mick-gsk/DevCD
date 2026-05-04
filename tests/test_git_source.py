from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from devcd.slices.git_source.service import GitEventSource


def run_git(repo_path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True)


def test_git_source_collects_branch_and_commit_events(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git executable is not available")

    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "devcd@example.invalid")
    run_git(tmp_path, "config", "user.name", "DevCD Test")
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    run_git(tmp_path, "add", "README.md")
    run_git(tmp_path, "commit", "-m", "initial commit")

    events = GitEventSource().collect_snapshot_events(tmp_path)

    assert [event.type for event in events] == ["branch_change", "commit"]
    assert events[0].payload["branch"] in {"main", "master"}
    assert events[1].payload["message"] == "initial commit"


def test_git_source_returns_no_events_for_non_repo(tmp_path: Path) -> None:
    events = GitEventSource().collect_snapshot_events(tmp_path)

    assert events == []
