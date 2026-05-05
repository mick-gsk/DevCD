from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from devcd.slices.agentic_context.models import (
    RunnerCommandTemplate,
    ScoutReport,
    ScoutRunResult,
    ScoutRunStatus,
    ScoutTask,
)


class SubprocessScoutRunner:
    def __init__(
        self,
        template: RunnerCommandTemplate,
        *,
        timeout_seconds: float = 15.0,
        output_byte_limit: int = 65536,
        cwd: Path | None = None,
    ) -> None:
        self.template = template
        self.timeout_seconds = timeout_seconds
        self.output_byte_limit = output_byte_limit
        self.cwd = cwd

    def run(self, task: ScoutTask) -> ScoutRunResult:
        try:
            template = RunnerCommandTemplate.model_validate(self.template.model_dump())
        except ValidationError as error:
            return self._result(
                task,
                ScoutRunStatus.FAILED,
                error_summary=f"invalid runner template: {error.errors()[0]['msg']}",
            )
        argv = [template.command, *template.args]
        try:
            completed = subprocess.run(
                argv,
                input=task.model_dump_json(),
                capture_output=True,
                cwd=self.cwd,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._result(
                task,
                ScoutRunStatus.TIMED_OUT,
                error_summary="scout runner timed out before returning a report",
            )
        except OSError as error:
            return self._result(task, ScoutRunStatus.FAILED, error_summary=str(error))

        output = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if self._output_exceeds_limit(output, stderr):
            return self._result(
                task,
                ScoutRunStatus.OUTPUT_LIMIT_EXCEEDED,
                error_summary="scout runner output exceeded the configured byte limit",
            )
        if completed.returncode != 0:
            return self._result(
                task,
                ScoutRunStatus.FAILED,
                error_summary=f"scout runner exited with code {completed.returncode}",
            )
        try:
            payload = json.loads(output)
            report = ScoutReport.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, TypeError) as error:
            error_name = error.__class__.__name__
            return self._result(
                task,
                ScoutRunStatus.INVALID_REPORT,
                error_summary=f"scout runner returned an invalid report: {error_name}",
            )
        return self._result(task, ScoutRunStatus.SUCCEEDED, report=report)

    def _output_exceeds_limit(self, stdout: str, stderr: str) -> bool:
        return (
            len(stdout.encode("utf-8")) > self.output_byte_limit
            or len(stderr.encode("utf-8")) > self.output_byte_limit
        )

    def _result(
        self,
        task: ScoutTask,
        status: ScoutRunStatus,
        *,
        report: ScoutReport | None = None,
        error_summary: str | None = None,
    ) -> ScoutRunResult:
        result_data: dict[str, Any] = {
            "runner_id": self.template.id,
            "task_id": task.id,
            "status": status,
            "report": report,
            "error_summary": error_summary,
            "raw_output_stored": False,
        }
        return ScoutRunResult(**result_data)