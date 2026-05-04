from __future__ import annotations

import subprocess
from pathlib import Path

from devcd.slices.events.models import DevEvent, EventSource


class GitEventSource:
    def collect_snapshot_events(self, repo_path: Path) -> list[DevEvent]:
        resolved_repo = repo_path.resolve()
        branch = self._git(resolved_repo, "branch", "--show-current")
        commit_sha = self._git(resolved_repo, "rev-parse", "--short", "HEAD")
        commit_message = self._git(resolved_repo, "log", "-1", "--pretty=%s")
        if not branch and not commit_sha:
            return []

        events: list[DevEvent] = []
        if branch:
            events.append(
                DevEvent(
                    source=EventSource.GIT,
                    type="branch_change",
                    payload={"repo": str(resolved_repo), "branch": branch},
                )
            )
        if commit_sha:
            events.append(
                DevEvent(
                    source=EventSource.GIT,
                    type="commit",
                    payload={
                        "repo": str(resolved_repo),
                        "sha": commit_sha,
                        "message": commit_message,
                    },
                )
            )
        return events

    def _git(self, repo_path: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
