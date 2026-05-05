from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENTS = ROOT / "examples" / "agent-handoff" / "sample-events.jsonl"


def main() -> None:
    _run([sys.executable, "-m", "devcd.cli", "--help"])
    print("devcd --help: ok")

    packs = _run_json([sys.executable, "-m", "devcd.cli", "context", "packs", "--json"])
    pack_ids = {item["id"] for item in packs}
    missing_packs = {"developer", "research"} - pack_ids
    if missing_packs:
        raise SystemExit(f"Missing built-in Context Packs: {sorted(missing_packs)}")
    print("devcd context packs: ok")

    quickstart = _run_json(
        [
            sys.executable,
            "-m",
            "devcd.cli",
            "quickstart",
            "--no-tui",
            "--json",
            "--endpoint",
            "http://127.0.0.1:9/state",
            "--demo-events",
            str(DEMO_EVENTS),
        ]
    )
    required_keys = {"defaults", "live_first", "privacy", "steps", "value_proposition"}
    missing_keys = required_keys - set(quickstart)
    if missing_keys:
        raise SystemExit(f"Quickstart report missing keys: {sorted(missing_keys)}")
    if quickstart["privacy"].get("remote_export_enabled_by_default") is not False:
        raise SystemExit("Quickstart report must show remote export disabled by default")
    print("devcd quickstart: ok")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _run_json(command: list[str]) -> Any:
    result = _run(command)
    return json.loads(result.stdout)


if __name__ == "__main__":
    main()
