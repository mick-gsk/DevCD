from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_REQUIRED_WHEEL_MEMBERS = {
    "devcd/cli.py",
    "devcd/py.typed",
}
_REQUIRED_SDIST_MEMBERS = {
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dist_dir = root / "dist"
    wheel = _single_artifact(dist_dir, "devcd-*.whl")
    sdist = _single_artifact(dist_dir, "devcd-*.tar.gz")
    _check_wheel(wheel)
    _check_sdist(sdist)
    _smoke_test_wheel(wheel)
    print(f"Distribution check passed: {wheel.name} and {sdist.name}")
    return 0


def _single_artifact(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches) or "none"
        raise SystemExit(f"Expected exactly one {pattern} artifact in {dist_dir}; found {names}")
    return matches[0]


def _check_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    missing = sorted(_REQUIRED_WHEEL_MEMBERS - names)
    if missing:
        raise SystemExit(f"Wheel is missing required files: {', '.join(missing)}")
    forbidden = [name for name in names if name.startswith(("tests/", "docs/", "site/"))]
    if forbidden:
        raise SystemExit(f"Wheel contains non-runtime files: {', '.join(sorted(forbidden)[:5])}")


def _check_sdist(sdist: Path) -> None:
    completed = subprocess.run(
        ["tar", "-tf", str(sdist)],
        check=True,
        capture_output=True,
        text=True,
    )
    names = {name.partition("/")[2] for name in completed.stdout.splitlines() if "/" in name}
    missing = sorted(_REQUIRED_SDIST_MEMBERS - names)
    if missing:
        raise SystemExit(f"sdist is missing required files: {', '.join(missing)}")


def _smoke_test_wheel(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="devcd-dist-check-") as temporary_directory:
        temp_dir = Path(temporary_directory)
        venv_dir = temp_dir / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        python = _venv_python(venv_dir)
        devcd = _venv_script(venv_dir, "devcd")
        subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True)
        subprocess.run([str(devcd), "--help"], check=True, capture_output=True, text=True)
        packs = subprocess.run(
            [str(devcd), "context", "packs", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        pack_ids = {item["id"] for item in json.loads(packs.stdout)}
        if {"developer", "research"} - pack_ids:
            raise SystemExit("Wheel smoke test did not list built-in Context Packs")
        quickstart = subprocess.run(
            [
                str(devcd),
                "quickstart",
                "--no-tui",
                "--json",
                "--config",
                str(temp_dir / "devcd.toml"),
                "--endpoint",
                "http://127.0.0.1:9/state",
            ],
            check=True,
            capture_output=True,
            cwd=temp_dir,
            text=True,
        )
        payload = json.loads(quickstart.stdout)
        if payload.get("live_first", {}).get("daemon_required") is not False:
            raise SystemExit("Wheel smoke test did not return the live-first quickstart contract")


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_script(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


if __name__ == "__main__":
    raise SystemExit(main())
