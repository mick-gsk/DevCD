# OpenClaw Continuity Moment Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a publishable OpenClaw Skill draft and supporting docs that make DevCD's Turn-0 continuity behavior the main OpenClaw moment.

**Architecture:** This stays outside runtime code: no new slice, no OpenClaw config mutation, no MCP tool surface. The Skill teaches an OpenClaw agent to read the existing read-only DevCD MCP Action Packet before asking the developer to recap.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---

### Task 1: Guard The OpenClaw Skill Contract

**Files:**
- Create: `tests/test_openclaw_continuity_skill.py`
- Create: `skills/devcd-continuity/SKILL.md`

- [x] **Step 1: Write the failing tests**

Add tests that assert the Skill is small, has OpenClaw-compatible frontmatter, prefers the Action Packet, and avoids unsafe or false claims.

<pre><code>
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
</code></pre>

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_openclaw_continuity_skill.py -v`

Expected: FAIL because `skills/devcd-continuity/SKILL.md` does not exist.

- [x] **Step 3: Add the minimal Skill**

Create `skills/devcd-continuity/SKILL.md` with frontmatter and instructions for Turn-0 continuity.

- [x] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_openclaw_continuity_skill.py -v`

Expected: PASS.

### Task 2: Update OpenClaw Docs Around The Moment

**Files:**
- Modify: `docs/devcd/openclaw-integration.md`
- Modify: `docs/devcd/openclaw-usecase-draft.md`
- Modify: `docs/devcd/openclaw-packaging-spike.md`

- [x] **Step 1: Update integration docs**

Make the Turn-0 Action Packet the first-class path. Keep config manual and read-only.

- [x] **Step 2: Update use-case draft**

Replace legacy `agent-handoff-packet` language with `action-packet` where the goal is next-agent start behavior.

- [x] **Step 3: Update packaging spike**

Reflect that the next artifact is now a Skill draft under `skills/devcd-continuity/SKILL.md`, still not a ClawHub publication.

### Task 3: Validate The Moment

**Files:**
- Modify: `docs/superpowers/plans/2026-05-06-openclaw-continuity-moment.md`

- [x] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_openclaw_continuity_skill.py -v`

Expected: PASS.

- [x] **Step 2: Run full validation**

Run: `make check`

Expected: Ruff, mypy, and pytest pass.

- [x] **Step 3: Validate docs build without touching tracked site output**

Run: `mkdocs build --strict --site-dir <temp-dir>`

Expected: PASS. Existing warnings about non-nav internal pages are acceptable if no build error occurs.
