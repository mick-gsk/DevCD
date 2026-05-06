from __future__ import annotations

from pathlib import Path

SKILL_PATH = Path("skills/devcd-continuity/SKILL.md")


def test_openclaw_continuity_skill_has_required_frontmatter() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")

    assert text.startswith("---\n")
    assert "name: devcd-continuity" in text
    assert "description:" in text
    assert "devcd://context/action-packet" in text


def test_openclaw_continuity_skill_is_safe_and_honest() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "do not ask for hidden payloads" in lowered
    assert "do not edit openclaw config" in lowered
    assert "official openclaw plugin" not in lowered
    assert "published on clawhub" not in lowered
    assert "end-to-end verified" not in lowered
    assert "tools/call" not in lowered
