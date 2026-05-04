from __future__ import annotations

from devcd.slices.policy_layer.service import PolicyEngine


def test_default_policy_denies_remote_export_and_actions() -> None:
    policy = PolicyEngine.default()

    export_decision = policy.decide_remote_export("https://example.invalid")
    action_decision = policy.decide_action("commit")

    assert not export_decision.allowed
    assert "local-first" in export_decision.reason
    assert not action_decision.allowed
    assert "observe-only" in action_decision.reason
