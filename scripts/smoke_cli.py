from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def main() -> None:
    smoke = _run_json([sys.executable, "-m", "devcd.cli", "smoke", "--json"])
    if smoke.get("status") != "pass":
        raise SystemExit(json.dumps(smoke, indent=2, sort_keys=True))

    for check in smoke.get("checks", []):
        print(f"{check['label']}: ok")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _run_json(command: list[str]) -> Any:
    result = _run(command)
    return json.loads(result.stdout)


if __name__ == "__main__":
    main()
