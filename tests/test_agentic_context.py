from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

import pytest

from devcd.slices.agentic_context.models import (
    ActionPacket,
    RunnerCommandTemplate,
    ScoutEvidence,
    ScoutReport,
    ScoutRunStatus,
    ScoutTask,
    ScoutTaskKind,
)
from devcd.slices.agentic_context.runner import SubprocessScoutRunner
from devcd.slices.agentic_context.service import AgenticContextService
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def test_scout_task_defaults_to_metadata_only_context() -> None:
    task = ScoutTask(
        kind=ScoutTaskKind.IDENTIFY_CURRENT_GOAL,
        prompt="Find the active goal from visible local metadata.",
        surface="coding-agent",
        context_pack="developer",
        expected_evidence=["devcd_continuity"],
        policy_decision_id="policy-1",
    )

    assert task.schema_version == "1.0"
    assert task.data_class == "metadata"
    assert task.expires_at > task.created_at


def test_scout_report_requires_evidence() -> None:
    with pytest.raises(ValueError):
        ScoutReport(
            task_id="task-1",
            summary="Current goal is unclear.",
            confidence=0.4,
            evidence=[],
        )


def test_runner_template_rejects_shell_metacharacters() -> None:
    with pytest.raises(ValueError):
        RunnerCommandTemplate(
            id="unsafe",
            command="powershell",
            args=["-c", "echo ok; Remove-Item important"],
        )


def test_runner_template_rejects_shell_interpreters_even_without_metacharacters() -> None:
    with pytest.raises(ValueError):
        RunnerCommandTemplate(
            id="shell",
            command="powershell.exe",
            args=["-Command", "Get-ChildItem"],
        )


def test_runner_template_rejects_command_execution_flags() -> None:
    with pytest.raises(ValueError):
        RunnerCommandTemplate(
            id="python-c",
            command=sys.executable,
            args=["-c", "print('not an allowlisted runner script')"],
        )


def test_runner_template_allows_executable_path_with_spaces() -> None:
    template = RunnerCommandTemplate(
        id="windows-path",
        command=r"C:\Program Files\Agent Runner\runner.exe",
        args=["--json"],
    )

    assert template.command == r"C:\Program Files\Agent Runner\runner.exe"


def test_action_packet_is_ready_when_goal_and_next_action_exist() -> None:
    packet = ActionPacket(
        current_goal="Ship the agentic context runner MVP",
        next_action="Write the failing model tests",
        recommended_agent_mode="implementation",
        evidence=[
            ScoutEvidence(
                source="devcd",
                summary="Continuity packet identified the implementation task.",
                timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
                policy_reason="metadata-only local context is allowed",
            )
        ],
    )

    assert packet.ready_for_agent is True


def test_service_creates_default_scout_tasks_for_empty_context(tmp_path) -> None:
    service, _state_engine = build_agentic_context_service(tmp_path)

    tasks = service.create_scout_tasks(surface="coding-agent", context_pack="developer")

    assert [task.kind for task in tasks]
    assert all(task.data_class == "metadata" for task in tasks)


def test_service_rejects_scout_tasks_when_context_export_denied(tmp_path) -> None:
    policy_engine = PolicyEngine(
        allow_observation=True,
        allow_local_storage=True,
        allow_remote_export=False,
        allow_actions=False,
        allowed_data_classes={"secret"},
    )
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    ambient_service = AmbientContextService(
        state_engine,
        memory_store,
        policy_engine,
        feedback_path=tmp_path / "context-feedback.jsonl",
    )
    service = AgenticContextService(
        ambient_context_service=ambient_service,
        policy_engine=policy_engine,
    )

    with pytest.raises(ValueError):
        service.create_scout_tasks(surface="coding-agent", context_pack="developer")


def test_service_creates_action_packet_without_runner(tmp_path) -> None:
    service, _state_engine = build_agentic_context_service(tmp_path)

    packet = service.create_action_packet(surface="coding-agent", context_pack="developer")

    assert packet.schema_version == "1.0"
    assert packet.ready_for_agent in {True, False}
    assert packet.policy_summary is not None


def test_service_uses_visible_continuity_for_action_packet(tmp_path) -> None:
    service, state_engine = build_agentic_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Ship the local scout runner MVP"},
        )
    )

    packet = service.create_action_packet(surface="coding-agent", context_pack="developer")

    assert packet.current_goal == "Ship the local scout runner MVP"
    assert packet.evidence


def test_service_maps_resume_signals_into_action_packet(tmp_path) -> None:
    service, state_engine = build_agentic_context_service(tmp_path)
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="goal_update",
            timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
            payload={"current_goal": "Resume the release gate fix"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="patch_apply",
            timestamp=datetime(2026, 5, 5, 12, 1, tzinfo=UTC),
            payload={"summary": "Changed only the renderer output"},
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.TASK,
            type="test_failure",
            timestamp=datetime(2026, 5, 5, 12, 2, tzinfo=UTC),
            payload={
                "reason": "make check failed on policy assertions",
                "suggested_next_action": "Inspect the policy assertion before editing",
                "do_not_repeat": ["Do not tweak the renderer without checking the contract"],
            },
        )
    )
    state_engine.accept_event(
        DevEvent(
            source=EventSource.NOTES,
            type="note_update",
            timestamp=datetime(2026, 5, 5, 12, 3, tzinfo=UTC),
            payload={"title": "PRIVATE_NOTE_PAYLOAD"},
            sensitivity=EventSensitivity.SENSITIVE,
            data_class="metadata",
        )
    )

    packet = service.create_action_packet(surface="coding-agent", context_pack="developer")
    body = packet.model_dump(mode="json")

    assert body["blockers"][0]["summary"] == "make check failed on policy assertions"
    assert body["do_not_repeat"] == [
        "Do not tweak the renderer without checking the contract"
    ]
    assert body["withheld_context"][0]["category"] == "sensitivity"
    assert "sensitive events" in body["withheld_context"][0]["policy_reason"]
    assert "PRIVATE_NOTE_PAYLOAD" not in json.dumps(body)


def test_accept_scout_report_updates_next_action(tmp_path) -> None:
    service, _state_engine = build_agentic_context_service(tmp_path)
    report = ScoutReport(
        task_id="task-1",
        summary="The next implementation move is policy-gated report intake.",
        confidence=0.8,
        next_action="Implement report intake in the service.",
        evidence=[
            ScoutEvidence(
                source="devcd",
                summary="Scout task requested report intake validation.",
                timestamp=datetime(2026, 5, 5, 12, 1, tzinfo=UTC),
                policy_reason="metadata-only local context is allowed",
            )
        ],
    )

    accepted = service.accept_scout_report(report)
    packet = service.create_action_packet(surface="coding-agent", context_pack="developer")

    assert accepted.id == report.id
    assert packet.next_action == "Implement report intake in the service."


def test_accept_scout_report_rejects_missing_evidence(tmp_path) -> None:
    service, _state_engine = build_agentic_context_service(tmp_path)
    report = ScoutReport.model_construct(
        task_id="task-1",
        summary="Evidence-free report should not be accepted.",
        confidence=0.5,
        evidence=[],
        data_class="metadata",
    )

    with pytest.raises(ValueError):
        service.accept_scout_report(report)


def test_accept_scout_report_rejects_non_metadata_output(tmp_path) -> None:
    service, _state_engine = build_agentic_context_service(tmp_path)
    report = ScoutReport.model_construct(
        task_id="task-1",
        summary="Raw runner output should not be stored.",
        confidence=0.5,
        evidence=[
            ScoutEvidence(
                source="runner",
                summary="Runner emitted a raw output payload.",
                timestamp=datetime(2026, 5, 5, 12, 2, tzinfo=UTC),
                policy_reason="raw output is not allowed",
            )
        ],
        data_class="full_text",
    )

    with pytest.raises(ValueError):
        service.accept_scout_report(report)


def test_subprocess_runner_accepts_json_report(tmp_path) -> None:
    script = tmp_path / "scout_runner.py"
    script.write_text(
        """
import json
import sys

task = json.load(sys.stdin)
print(json.dumps({
    "task_id": task["id"],
    "summary": "Scout found a next action.",
    "confidence": 0.9,
    "next_action": "Implement the subprocess runner adapter.",
    "evidence": [{
        "source": "runner",
        "summary": "Runner processed the scout task.",
        "timestamp": "2026-05-05T12:03:00Z",
        "policy_reason": "metadata-only runner output is allowed"
    }]
}))
""".strip(),
        encoding="utf-8",
    )
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="fake", command=sys.executable, args=[str(script)]),
    )

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.SUCCEEDED
    assert result.report is not None
    assert result.report.next_action == "Implement the subprocess runner adapter."


def test_subprocess_runner_times_out_safely(tmp_path) -> None:
    script = tmp_path / "slow_runner.py"
    script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="slow", command=sys.executable, args=[str(script)]),
        timeout_seconds=0.1,
    )

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.TIMED_OUT
    assert result.report is None
    assert result.raw_output_stored is False


def test_subprocess_runner_rejects_invalid_json(tmp_path) -> None:
    script = tmp_path / "invalid_runner.py"
    script.write_text("print('not json')\n", encoding="utf-8")
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="invalid", command=sys.executable, args=[str(script)]),
    )

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.INVALID_REPORT
    assert result.report is None


def test_subprocess_runner_rejects_oversized_output(tmp_path) -> None:
    script = tmp_path / "large_runner.py"
    script.write_text("print('x' * 2000)\n", encoding="utf-8")
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="large", command=sys.executable, args=[str(script)]),
        output_byte_limit=128,
    )

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.OUTPUT_LIMIT_EXCEEDED
    assert result.report is None
    assert result.raw_output_stored is False


def test_subprocess_runner_rejects_oversized_stderr(tmp_path) -> None:
    script = tmp_path / "large_stderr_runner.py"
    script.write_text("import sys\nsys.stderr.write('x' * 2000)\n", encoding="utf-8")
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="large-stderr", command=sys.executable, args=[str(script)]),
        output_byte_limit=128,
    )

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.OUTPUT_LIMIT_EXCEEDED
    assert result.report is None
    assert result.raw_output_stored is False


def test_subprocess_runner_revalidates_template_before_execution(tmp_path) -> None:
    runner = SubprocessScoutRunner(
        RunnerCommandTemplate(id="local", command=sys.executable, args=[]),
        cwd=tmp_path,
    )
    object.__setattr__(runner.template, "command", "powershell")

    result = runner.run(_sample_scout_task())

    assert result.status is ScoutRunStatus.FAILED
    assert result.error_summary is not None
    assert "invalid runner template" in result.error_summary


def build_agentic_context_service(tmp_path) -> tuple[AgenticContextService, StateEngine]:
    policy_engine = PolicyEngine.default()
    memory_store = MemoryStore.with_ttl_seconds(315360000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy_engine, memory_store, event_ledger)
    ambient_service = AmbientContextService(
        state_engine,
        memory_store,
        policy_engine,
        feedback_path=tmp_path / "context-feedback.jsonl",
    )
    return (
        AgenticContextService(
            ambient_context_service=ambient_service,
            policy_engine=policy_engine,
        ),
        state_engine,
    )


def _sample_scout_task() -> ScoutTask:
    return ScoutTask(
        kind=ScoutTaskKind.PROPOSE_NEXT_ACTION,
        prompt="Propose the next safe action.",
        surface="coding-agent",
        context_pack="developer",
        expected_evidence=["devcd_continuity"],
        policy_decision_id="policy-1",
    )
