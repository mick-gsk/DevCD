"""
Self-healer for pyproject.toml structural issues.

Detects and fixes keys that were accidentally placed in the wrong TOML section.
Known failure pattern: `dependencies` or `optional-dependencies` end up inside
[project.urls] instead of [project], causing hatchling to reject them as
non-string URL values.

Outputs `fixed=true` to GITHUB_OUTPUT if a fix was applied.
"""

import os
import sys
import tomllib
from pathlib import Path

try:
    import tomli_w
except ImportError:
    print("tomli-w is not installed — cannot write TOML fix", file=sys.stderr)
    sys.exit(1)

# Keys that belong in [project], not in [project.urls]
PROJECT_KEYS = {"dependencies", "optional-dependencies"}

GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "")


def set_output(key: str, value: str) -> None:
    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


path = Path("pyproject.toml")

with path.open("rb") as f:
    data = tomllib.load(f)

project = data.get("project", {})
urls = project.get("urls", {})

# Detect non-string values inside [project.urls] that belong in [project]
misplaced = {k: v for k, v in urls.items() if not isinstance(v, str)}

if not misplaced:
    print("pyproject.toml structure is valid — nothing to heal")
    set_output("fixed", "false")
    sys.exit(0)

print(f"Found misplaced keys in [project.urls]: {list(misplaced)}")

# Fix: strip misplaced entries from [project.urls], restore them to [project]
fixed_project = dict(project)
fixed_project["urls"] = {k: v for k, v in urls.items() if isinstance(v, str)}
for k, v in misplaced.items():
    if k not in fixed_project:
        fixed_project[k] = v

data["project"] = fixed_project

path.write_bytes(tomli_w.dumps(data).encode("utf-8"))

# Verify the fix is parseable
with path.open("rb") as f:
    tomllib.load(f)

print(f"Healed: restored {list(misplaced)} from [project.urls] to [project]")
set_output("fixed", "true")
