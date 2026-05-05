# Operational Readiness CLI Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `devcd status` and `devcd doctor` so users can diagnose local DevCD runtime readiness without remote export or telemetry.

**Architecture:** Implement top-level Typer commands in `packages/devcd-core/src/devcd/cli.py` using existing local services. Keep readiness checks read-only except explicit in-memory or temporary-directory safe checks. Cover the CLI contract in `tests/test_cli.py` and document the product decision in ADR-006.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---

### Task 1: Status Command Contract

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`

- [ ] **Step 1: Write failing tests**

Add tests that run `devcd status` without a daemon and with a local ledger containing demo state.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_status_reports_no_daemon_with_next_step tests/test_cli.py::test_status_reports_local_demo_state -v
```

Expected: FAIL because `status` is not registered.

- [ ] **Step 3: Implement minimal status command**

Add a top-level Typer command that resolves config/token state, probes loopback `/state`, summarizes local ledger-derived state, and renders a concrete next command.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm both tests pass.

### Task 2: Doctor Command Contract

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`

- [ ] **Step 1: Write failing tests**

Add tests for missing config/token reporting, sensitive policy denial, handoff demo validation, and JSON output.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_doctor_reports_missing_token_and_config tests/test_cli.py::test_doctor_json_verifies_sensitive_policy_denial tests/test_cli.py::test_doctor_validates_handoff_demo -v
```

Expected: FAIL because `doctor` is not registered.

- [ ] **Step 3: Implement minimal doctor command**

Add typed check dictionaries with stable `id`, `status`, `summary`, `details`, and `next_step` fields. Render JSON with `--json` and human output otherwise.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm all doctor tests pass.

### Task 3: Documentation Consistency

**Files:**
- Modify: `docs/getting-started.md`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add docs command consistency expectation**

Extend doctor tests to verify docs mention `devcd status` and `devcd doctor`.

- [ ] **Step 2: Update docs**

Add readiness commands to Getting Started near the daemon startup flow and troubleshooting section.

- [ ] **Step 3: Verify full gate**

Run:

```bash
make check
```

Expected: Ruff, mypy, and pytest pass.
