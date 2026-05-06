# Warm Start First Run Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DevCD's first-run output feel like a usable agent warm start instead of a setup/status dump.

**Architecture:** Keep the existing CLI and local-first boundaries. Extend the `onboard` report with a policy-safe warm-start receipt derived from existing quickstart/local-state data, then update README and getting-started copy so Action Packet is the main first success path.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---

### Task 1: Onboard Warm-Start Receipt

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`

- [x] **Step 1: Write failing tests**

Add assertions that `devcd onboard --json` exposes a `warm_start` object with daemonless/external-mutation trust receipts, agent readiness, primary command, empty-ledger guidance, and seed commands.

- [x] **Step 2: Verify RED**

Run: `pytest tests/test_cli.py::test_onboard_json_contract_is_stable tests/test_cli.py::test_onboard_creates_config_and_agent_ready_workspace -q`

Expected: failure because `warm_start` is missing.

Observed: failed because `warm_start` and the rendered `Warm start` block were missing.

- [x] **Step 3: Implement minimal code**

Build `warm_start` inside `_build_onboard_report()` from the existing agent-ready report and quickstart state. Render a short `Warm start` block in `_render_onboard_report()`.

- [x] **Step 4: Verify GREEN**

Run the same focused pytest command and confirm both tests pass.

### Task 2: First-Run Copy Refresh

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`

- [x] **Step 1: Rewrite first viewport and quick start around Action Packet**

Lead with agent continuity for mixed setups, a daemonless warm-start path, and a clear Advanced/live daemon branch.

- [x] **Step 2: Verify docs are consistent with CLI**

Check command names and boundaries against `packages/devcd-core/src/devcd/cli.py`.

### Task 3: Final Verification

**Files:**
- Read: changed files and test output

- [x] **Step 1: Run focused tests**

Run: `pytest tests/test_cli.py::test_onboard_json_contract_is_stable tests/test_cli.py::test_onboard_creates_config_and_agent_ready_workspace tests/test_cli.py::test_quickstart_is_live_first_and_reports_next_steps -q`

- [x] **Step 2: Run full repo check**

Run: `make check`

Observed: Ruff passed, mypy passed, and pytest reported `242 passed`.

- [x] **Step 3: Review requirements coverage**

Confirmed: the implementation adds a product-level warm-start receipt to `devcd onboard` before docs-only messaging and preserves local-first/no-external-mutation boundaries.
