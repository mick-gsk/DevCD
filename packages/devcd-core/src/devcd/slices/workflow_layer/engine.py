from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import yaml

from devcd.slices.workflow_layer.models import (
    CommandStep,
    GateStep,
    RunState,
    RunStatus,
    ShellStep,
    StepDefinition,
    StepResult,
    StepStatus,
    WorkflowDefinition,
)

if TYPE_CHECKING:
    from devcd.slices.policy_layer.service import PolicyEngine


class CommandExecutionResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[CommandStep], CommandExecutionResult]


class WorkflowEngine:
    def __init__(
        self,
        runs_dir: Path,
        policy_engine: PolicyEngine | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._runs_dir = runs_dir
        self._policy_engine = policy_engine
        self._command_runner = command_runner

    def execute(
        self,
        definition: WorkflowDefinition,
        run_id: str | None = None,
    ) -> RunState:
        state = RunState(
            run_id=run_id or _new_run_id(),
            workflow_name=definition.name,
            status=RunStatus.RUNNING,
            current_step_index=0,
        )
        run_dir = self._run_dir(state.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_workflow_snapshot(run_dir, definition)
        self._save_run_state(run_dir, state)
        return self._run_steps(state, definition, run_dir)

    def resume(self, run_id: str) -> RunState:
        run_dir = self._run_dir(run_id)
        state = self._load_run_state(run_dir)
        if state.is_terminal():
            return state
        if state.status is not RunStatus.PAUSED:
            return state
        definition = _load_workflow_snapshot(run_dir)
        state.status = RunStatus.RUNNING
        state.updated_at = datetime.now(UTC)
        self._save_run_state(run_dir, state)
        return self._run_steps(state, definition, run_dir)

    def load_state(self, run_id: str) -> RunState:
        return self._load_run_state(self._run_dir(run_id))

    def list_runs(self) -> list[RunState]:
        states: list[RunState] = []
        if not self._runs_dir.exists():
            return states
        for run_dir in sorted(self._runs_dir.iterdir()):
            state_file = run_dir / "state.json"
            if state_file.is_file():
                try:
                    states.append(
                        RunState.model_validate_json(state_file.read_text(encoding="utf-8"))
                    )
                except Exception:  # noqa: BLE001  # bare-except for resilient listing
                    continue
        return states

    def _run_steps(
        self, state: RunState, definition: WorkflowDefinition, run_dir: Path
    ) -> RunState:
        steps = definition.steps
        while state.current_step_index < len(steps):
            step = steps[state.current_step_index]
            decision = self._policy_decision(step)
            if decision == "deny":
                result = StepResult(
                    step_index=state.current_step_index,
                    step_type=step.type,
                    status=StepStatus.ABORTED,
                    error="policy denied execution of this step",
                    started_at=datetime.now(UTC),
                    ended_at=datetime.now(UTC),
                )
                state.step_results.append(result)
                state.status = RunStatus.ABORTED
                state.updated_at = datetime.now(UTC)
                self._save_run_state(run_dir, state)
                return state

            if isinstance(step, GateStep):
                result = StepResult(
                    step_index=state.current_step_index,
                    step_type="gate",
                    status=StepStatus.SKIPPED,
                    output=step.message,
                    started_at=datetime.now(UTC),
                    ended_at=datetime.now(UTC),
                )
                state.step_results.append(result)
                state.current_step_index += 1
                state.status = RunStatus.PAUSED
                state.updated_at = datetime.now(UTC)
                self._save_run_state(run_dir, state)
                return state

            result = self._execute_step(step, state.current_step_index)
            state.step_results.append(result)
            state.updated_at = datetime.now(UTC)

            if result.status is StepStatus.FAILED:
                state.status = RunStatus.FAILED
                self._save_run_state(run_dir, state)
                return state

            state.current_step_index += 1
            self._save_run_state(run_dir, state)

        state.status = RunStatus.COMPLETED
        state.updated_at = datetime.now(UTC)
        self._save_run_state(run_dir, state)
        return state

    def _policy_decision(self, step: StepDefinition) -> str:
        if self._policy_engine is None:
            if isinstance(step, ShellStep):
                return "deny"
            return "allow"
        decision = self._policy_engine.decide_workflow_step_execute(step)
        return "allow" if decision.allowed else "deny"

    def _execute_step(self, step: StepDefinition, index: int) -> StepResult:
        started = datetime.now(UTC)
        if isinstance(step, CommandStep):
            return self._run_command_step(step, index, started)
        if isinstance(step, ShellStep):
            return self._run_shell_step(step, index, started)
        return StepResult(
            step_index=index,
            step_type=step.type,
            status=StepStatus.FAILED,
            error=f"unhandled step type: {step.type}",
            started_at=started,
            ended_at=datetime.now(UTC),
        )

    def _run_command_step(self, step: CommandStep, index: int, started: datetime) -> StepResult:
        try:
            if self._command_runner is not None:
                proc = self._command_runner(step)
            else:
                proc = self._run_command_subprocess(step)
            status = StepStatus.COMPLETED if proc.returncode == 0 else StepStatus.FAILED
            return StepResult(
                step_index=index,
                step_type="command",
                status=status,
                output=proc.stdout,
                error=proc.stderr if proc.returncode != 0 else "",
                started_at=started,
                ended_at=datetime.now(UTC),
            )
        except subprocess.TimeoutExpired:
            return StepResult(
                step_index=index,
                step_type="command",
                status=StepStatus.FAILED,
                error=f"command timed out after {step.timeout_seconds}s",
                started_at=started,
                ended_at=datetime.now(UTC),
            )
        except TimeoutError:
            return StepResult(
                step_index=index,
                step_type="command",
                status=StepStatus.FAILED,
                error=f"command timed out after {step.timeout_seconds}s",
                started_at=started,
                ended_at=datetime.now(UTC),
            )

    def _run_command_subprocess(self, step: CommandStep) -> CommandExecutionResult:
        cmd = ["devcd"] + [step.name] + step.args
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=step.timeout_seconds,
            check=False,
        )
        return CommandExecutionResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def _run_shell_step(self, step: ShellStep, index: int, started: datetime) -> StepResult:
        try:
            proc = subprocess.run(
                step.run,
                shell=True,  # noqa: S602
                capture_output=True,
                text=True,
                timeout=step.timeout_seconds,
                cwd=step.working_dir,
                check=False,
            )
            status = StepStatus.COMPLETED if proc.returncode == 0 else StepStatus.FAILED
            return StepResult(
                step_index=index,
                step_type="shell",
                status=status,
                output=proc.stdout,
                error=proc.stderr if proc.returncode != 0 else "",
                started_at=started,
                ended_at=datetime.now(UTC),
            )
        except subprocess.TimeoutExpired:
            return StepResult(
                step_index=index,
                step_type="shell",
                status=StepStatus.FAILED,
                error=f"shell step timed out after {step.timeout_seconds}s",
                started_at=started,
                ended_at=datetime.now(UTC),
            )

    def _run_dir(self, run_id: str) -> Path:
        return self._runs_dir / run_id

    def _save_run_state(self, run_dir: Path, state: RunState) -> None:
        (run_dir / "state.json").write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _load_run_state(self, run_dir: Path) -> RunState:
        return RunState.model_validate_json(
            (run_dir / "state.json").read_text(encoding="utf-8")
        )


def _new_run_id() -> str:
    from uuid import uuid4

    return str(uuid4())


def _write_workflow_snapshot(run_dir: Path, definition: WorkflowDefinition) -> None:
    snapshot = json.loads(definition.model_dump_json())
    (run_dir / "workflow.yaml").write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _load_workflow_snapshot(run_dir: Path) -> WorkflowDefinition:
    raw = yaml.safe_load((run_dir / "workflow.yaml").read_text(encoding="utf-8"))
    return WorkflowDefinition.model_validate(raw)
