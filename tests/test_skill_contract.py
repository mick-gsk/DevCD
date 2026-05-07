from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _skill_files() -> list[Path]:
    files = sorted(path for path in REPO_ROOT.rglob("SKILL.md") if "skills" in path.parts)
    return files


def _frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    assert lines and lines[0] == "---"
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx] == "---":
            end_idx = idx
            break
    assert end_idx is not None, "missing closing frontmatter delimiter"
    return lines[1:end_idx]


def _level3_items(text: str) -> list[str]:
    lines = text.splitlines()
    header = "### Level 3 - Referenced Supporting Files"
    start = lines.index(header)
    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            break
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def test_all_skills_use_progressive_disclosure_contract() -> None:
    files = _skill_files()
    assert files, "expected at least one SKILL.md file"

    for path in files:
        text = path.read_text(encoding="utf-8")
        frontmatter = _frontmatter_lines(text)
        assert any(line.startswith("name:") for line in frontmatter), f"missing name in {path}"
        assert any(
            line.startswith("description:") for line in frontmatter
        ), f"missing description in {path}"

        assert "## Progressive Disclosure" in text, f"missing progressive section in {path}"
        assert "### Level 1 - Metadata (Auto-Loaded)" in text, f"missing level 1 in {path}"
        assert "### Level 2 - Full Instructions" in text, f"missing level 2 in {path}"
        assert (
            "### Level 3 - Referenced Supporting Files" in text
        ), f"missing level 3 in {path}"


def test_level3_references_are_none_or_existing_files() -> None:
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        items = _level3_items(text)
        assert items, f"level 3 section must contain at least one bullet in {path}"

        for item in items:
            if item.lower() == "none.":
                continue
            target = REPO_ROOT / item
            assert target.exists(), f"level 3 reference not found from {path}: {item}"
