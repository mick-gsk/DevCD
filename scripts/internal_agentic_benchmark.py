from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from devcd.kernel.settings import DevCDSettings
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent
from devcd.slices.policy_layer.models import PolicyDecision


def main() -> int:
    args = _parse_args()
    try:
        report = _build_report(
            config=Path(args.config) if args.config is not None else None,
            baseline_session=args.baseline_session,
            treatment_session=args.treatment_session,
        )
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_report(report))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Internal-only benchmark utility. Compares two captured sessions "
            "without adding any public product CLI surface."
        )
    )
    parser.add_argument(
        "--baseline-session",
        default="cold-start",
        help="Session id for the cold-start baseline run.",
    )
    parser.add_argument(
        "--treatment-session",
        default="devcd",
        help="Session id for the treatment run.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to devcd.toml.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    return parser.parse_args()


def _build_report(
    *,
    config: Path | None,
    baseline_session: str,
    treatment_session: str,
) -> dict[str, Any]:
    settings = DevCDSettings.load(config)
    records = list(EventLedger(settings.ledger_path).read_records())
    baseline = _session_metrics(records=records, session=baseline_session)
    treatment = _session_metrics(records=records, session=treatment_session)

    success_rate_delta = round(
        float(treatment["success_rate"]) - float(baseline["success_rate"]),
        4,
    )
    failed_attempts_delta = int(treatment["failed_attempts"]) - int(baseline["failed_attempts"])
    elapsed_seconds_delta = round(
        float(treatment["elapsed_seconds"]) - float(baseline["elapsed_seconds"]),
        3,
    )

    improved = success_rate_delta >= 0 and failed_attempts_delta <= 0
    if improved and elapsed_seconds_delta <= 0:
        verdict = "improved"
    elif improved:
        verdict = "mixed"
    else:
        verdict = "regressed"

    return {
        "scope": "internal-only",
        "baseline": baseline,
        "treatment": treatment,
        "comparison": {
            "success_rate_delta": success_rate_delta,
            "failed_attempts_delta": failed_attempts_delta,
            "elapsed_seconds_delta": elapsed_seconds_delta,
            "verdict": verdict,
        },
    }


def _session_metrics(
    *, records: list[tuple[DevEvent, PolicyDecision]], session: str
) -> dict[str, Any]:
    session_events: list[DevEvent] = []
    for event, _decision in records:
        capture_kind = event.payload.get("capture_kind")
        if not isinstance(capture_kind, str):
            continue
        capture_session = event.payload.get("session")
        if capture_session == session:
            session_events.append(event)

    if not session_events:
        raise ValueError(f"No capture events found for session '{session}'")

    attempt_events = [
        event for event in session_events if event.payload.get("capture_kind") == "attempt"
    ]
    succeeded_attempts = sum(
        1 for event in attempt_events if event.payload.get("outcome") == "succeeded"
    )
    failed_attempts = sum(1 for event in attempt_events if event.payload.get("outcome") == "failed")

    first_timestamp = min(event.timestamp for event in session_events)
    last_timestamp = max(event.timestamp for event in session_events)
    elapsed_seconds = round((last_timestamp - first_timestamp).total_seconds(), 3)

    return {
        "session": session,
        "total_capture_events": len(session_events),
        "attempt_events": len(attempt_events),
        "succeeded_attempts": succeeded_attempts,
        "failed_attempts": failed_attempts,
        "success_rate": _safe_ratio(succeeded_attempts, len(attempt_events)),
        "first_event_timestamp": first_timestamp.isoformat(),
        "last_event_timestamp": last_timestamp.isoformat(),
        "elapsed_seconds": elapsed_seconds,
    }


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(part / total, 4)


def _render_report(report: dict[str, Any]) -> str:
    baseline = report["baseline"]
    treatment = report["treatment"]
    comparison = report["comparison"]
    lines = [
        "DevCD internal benchmark",
        "- scope: internal-only",
        f"- baseline_session: {baseline['session']}",
        f"- treatment_session: {treatment['session']}",
        f"- baseline_success_rate: {baseline['success_rate']}",
        f"- treatment_success_rate: {treatment['success_rate']}",
        f"- success_rate_delta: {comparison['success_rate_delta']}",
        f"- failed_attempts_delta: {comparison['failed_attempts_delta']}",
        f"- elapsed_seconds_delta: {comparison['elapsed_seconds_delta']}",
        f"- verdict: {comparison['verdict']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
