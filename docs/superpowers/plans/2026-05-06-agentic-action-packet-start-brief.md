# Agentic Action Packet Start Brief Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `devcd agentic action-packet` useful as a direct start brief for the next coding agent, without adding new trust boundaries or changing MCP behavior.

**Architecture:** Keep the existing `agentic_context` slice and derive the Action Packet from the policy-filtered Continuity Packet. Task 1 improves the human-readable CLI rendering; Task 2 extends the `ActionPacket` contract with first-class blockers, `do_not_repeat`, and policy-safe withheld-context summaries for CLI, API, and MCP consumers.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---

### Task 1: Human-Readable Agent Start Brief

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`

- [x] **Step 1: Write the failing test**

Add a test near the existing `agentic action-packet` CLI tests:

<pre><code>
def test_agentic_action_packet_human_output_is_agent_start_brief(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    config_path = tmp_path / "devcd.toml"
    config_path.write_text(
        '[devcd]\nruntime_dir = "runtime"\nworking_memory_ttl_seconds = 315360000\n',
        encoding="utf-8",
    )
    (runtime_dir / "events.jsonl").write_text(
        "\n".join(
            [
                live_ledger_record(
                    source="task",
                    event_type="goal_update",
                    timestamp="2026-05-05T10:00:00Z",
                    payload={"current_goal": "Resume the release gate fix"},
                ),
                live_ledger_record(
                    source="task",
                    event_type="test_failure",
                    timestamp="2026-05-05T10:02:00Z",
                    payload={
                        "reason": "make check failed on policy assertions",
                        "suggested_next_action": "Inspect the policy assertion before editing",
                    },
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["agentic", "action-packet", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "# DevCD Action Packet" in result.output
    assert "## Start Brief" in result.output
    assert "- ready_for_agent: true" in result.output
    assert "- recommended_agent_mode: debugging" in result.output
    assert "Resume the release gate fix" in result.output
    assert "Inspect the policy assertion before editing" in result.output
    assert "## Evidence" in result.output
    assert "make check failed on policy assertions" in result.output
    assert "## Policy" in result.output
</code></pre>

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_agentic_action_packet_human_output_is_agent_start_brief -v`

Expected: FAIL because the existing command prints only the short `Action Packet` three-line format and lacks the Markdown sections.

- [x] **Step 3: Write minimal implementation**

Add a helper to `packages/devcd-core/src/devcd/cli.py`:

<pre><code>
def _render_action_packet(packet: ActionPacket) -> str:
    lines = [
        "# DevCD Action Packet",
        "",
        "## Start Brief",
        f"- ready_for_agent: {str(packet.ready_for_agent).lower()}",
        f"- recommended_agent_mode: {packet.recommended_agent_mode}",
        f"- current_goal: {packet.current_goal or 'unknown'}",
        f"- next_action: {packet.next_action or 'Use Scout Tasks to gather context.'}",
        "",
        "## Evidence",
    ]
    if packet.evidence:
        for evidence in packet.evidence:
            lines.append(f"- {evidence.source}: {evidence.summary}")
    else:
        lines.append("- No policy-visible evidence is available yet.")
    lines.extend(["", "## Policy"])
    lines.append(f"- {packet.policy_summary or 'No policy summary was attached.'}")
    return "\n".join(lines)
</code></pre>

Then replace the manual `typer.echo()` lines in `agentic_action_packet()` with `typer.echo(_render_action_packet(packet))` for non-JSON output.

- [x] **Step 4: Run the focused test**

Run: `pytest tests/test_cli.py::test_agentic_action_packet_human_output_is_agent_start_brief -v`

Expected: PASS.

- [x] **Step 5: Run focused neighboring tests**

Run: `pytest tests/test_cli.py::test_agentic_action_packet_json_returns_ready_field tests/test_cli.py::test_agentic_tasks_json_returns_scout_tasks -v`

Expected: PASS; JSON output remains unchanged.

- [x] **Step 6: Run full validation**

Run: `make check`

Expected: Ruff, mypy, and pytest pass.

### Task 2: First-Class Resume Signals In ActionPacket

**Files:**
- Modify: `docs/decisions/ADR-011-local-agentic-context-runner.md`
- Modify: `tests/test_agentic_context.py`
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/slices/agentic_context/models.py`
- Modify: `packages/devcd-core/src/devcd/slices/agentic_context/service.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`

- [x] **Step 1: Update ADR-011**

Record that Action Packets carry current goal, next action, recommended mode,
evidence, blockers, `do_not_repeat`, policy-safe withheld-context summaries, and
policy summary. Keep raw withheld payloads out of scope.

- [x] **Step 2: Write failing model/service tests**

Add tests that expect `ActionPacket` JSON to include `blockers`,
`do_not_repeat`, and `withheld_context`, and that `AgenticContextService` maps
these values from the policy-filtered Continuity Packet.

- [x] **Step 3: Write failing CLI test assertion**

Extend the human-readable CLI test to expect `## Blockers`, `## Do Not Repeat`,
and `## Withheld Context` sections.

- [x] **Step 4: Run failing tests**

Run: `pytest tests/test_agentic_context.py::test_service_maps_resume_signals_into_action_packet tests/test_cli.py::test_agentic_action_packet_human_output_is_agent_start_brief -v`

Expected: FAIL because the model and renderer do not expose the new sections yet.

- [x] **Step 5: Implement model and mapping**

Add slice-owned safe summary models to `agentic_context/models.py`, then map
`ContinuityPacket.blockers`, `ContinuityPacket.do_not_repeat`, and
`ContinuityPacket.withheld_context` in `AgenticContextService.create_action_packet()`.

- [x] **Step 6: Extend CLI renderer**

Render the new fields as Markdown sections for shell-capable agents while
keeping `--json` output machine-readable through the model dump.

- [x] **Step 7: Run focused and full validation**

Run focused tests, then `make check`.

### Task 3: API/MCP Contract And Golden Path Demo

**Files:**
- Modify: `tests/test_api.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `tests/test_cli.py`
- Modify: `packages/devcd-core/src/devcd/cli.py`
- Add: `examples/agentic-action-packet/sample-events.jsonl`
- Add: `examples/agentic-action-packet/action-packet.md`
- Add: `examples/agentic-action-packet/README.md`
- Add: `docs/devcd/agent-landscape.md`
- Modify: `docs/devcd/agent-consumption.md`
- Modify: `docs/getting-started.md`
- Modify: `mkdocs.yml`

- [x] **Step 1: Tighten API and MCP tests**

Assert that `/agentic-context/action-packet` and `devcd://context/action-packet`
include `blockers`, `do_not_repeat`, and `withheld_context`, and that sensitive
payload text is absent from the exported contract.

- [x] **Step 2: Write failing demo CLI tests**

Add tests for `devcd agentic action-packet-demo --events <jsonl>` in Markdown
and JSON modes. The tests use a checked-in JSONL fixture and assert a safe,
daemonless Action Packet.

- [x] **Step 3: Implement daemonless demo command**

Build an in-memory demo `AgenticContextService`, replay raw `DevEvent` JSONL,
and render the same Action Packet contract as the live command without reading
the real ledger, starting a daemon, or mutating the workspace.

- [x] **Step 4: Add golden path fixture and docs**

Check in a small fixture where a previous agent lost context after a failing
attempt. Document the expected Markdown output and the product decision from
current agent landscape research: DevCD should be the runtime-neutral continuity
layer, not another executor.

- [x] **Step 5: Run focused and full validation**

Run changed focused tests, then `make check`.