# DevCD Agent Handoff Brief

## brief_id
demo-handoff-brief

## active_goal
Ship the agent-switch review handoff demo

## relevant_artifacts
- file: examples/agent-switch/expected-review-agent-handoff.md - file_focus: examples/agent-switch/expected-review-agent-handoff.md
- file: tests/test_cli.py - file_focus: tests/test_cli.py
- file: packages/devcd-core/src/devcd/slices/ambient_context/service.py - file_focus: packages/devcd-core/src/devcd/slices/ambient_context/service.py

## git_context
- branch: agent-switch-demo
- latest_commit: def5678
- latest_commit_summary: add surface-specific handoff fixtures

## recent_attempts
- failure: test_failure: review-agent expected handoff still missing review artifacts (task/test_failure)
- unknown: fix_attempt: Created a coding-agent-only handoff and skipped review-agent output (task/fix_attempt)
- failure: test_failure: review-agent handoff lacks expected fixture comparison (task/test_failure)
- unknown: commit (git/commit)
- unknown: branch_change: agent-switch-demo (git/branch_change)

## Last attempt
- failure: review-agent expected handoff still missing review artifacts (task/test_failure)

## Last failure
- review-agent expected handoff still missing review artifacts

## Last attempted fix
- Created a coding-agent-only handoff and skipped review-agent output

## why_attempt_failed
- The latest failure happened after the attempted fix, so the fix did not resolve the blocker: review-agent expected handoff still missing review artifacts

## do_not_repeat
- Do not repeat the last attempted fix unchanged: Created a coding-agent-only handoff and skipped review-agent output (rationale: The latest failure happened after the attempted fix, so the fix did not resolve the blocker: review-agent expected handoff still missing review artifacts)

## Suggested next action
- Add review-agent expected output and compare surfaces

## unknowns
- Original chat history is not available in the handoff packet.

## blockers
- None detected.

## suggested_next_steps
- Continue from the active goal using visible artifacts and attempts.

## context_quality_notes
- No context feedback recorded.

## withheld_context
- category: sensitivity
  policy_reason: sensitive events are denied by the default local policy
  safe_summary: notes note_update signal was withheld; only source/type metadata is visible as a safe replacement.
- category: sensitivity
  policy_reason: sensitive events are denied by the default local policy
  safe_summary: task test_output signal was withheld; only source/type metadata is visible as a safe replacement.
- category: source
  policy_reason: source is not enabled by policy
  safe_summary: browser url_focus signal was withheld; only source/type metadata is visible as a safe replacement.
- category: state_area
  policy_reason: state area 'active_intent' is outside the 'review-agent' context surface
  safe_summary: A broader state area was withheld for this surface.
- category: state_area
  policy_reason: state area 'blockers' is outside the 'review-agent' context surface
  safe_summary: A broader state area was withheld for this surface.
- category: state_area
  policy_reason: state area 'suggested_next_steps' is outside the 'review-agent' context surface
  safe_summary: A broader state area was withheld for this surface.

## agent_limitations
- The agent cannot see sensitivity context withheld by policy (sensitive events are denied by the default local policy); safe summary: notes note_update signal was withheld; only source/type metadata is visible as a safe replacement.
- The agent cannot see sensitivity context withheld by policy (sensitive events are denied by the default local policy); safe summary: task test_output signal was withheld; only source/type metadata is visible as a safe replacement.
- The agent cannot see source context withheld by policy (source is not enabled by policy); safe summary: browser url_focus signal was withheld; only source/type metadata is visible as a safe replacement.
- The agent cannot see state_area context withheld by policy (state area 'active_intent' is outside the 'review-agent' context surface); safe summary: A broader state area was withheld for this surface.
- The agent cannot see state_area context withheld by policy (state area 'blockers' is outside the 'review-agent' context surface); safe summary: A broader state area was withheld for this surface.
- The agent cannot see state_area context withheld by policy (state area 'suggested_next_steps' is outside the 'review-agent' context surface); safe summary: A broader state area was withheld for this surface.

## policy_decision
- allowed: true
- operation: export
- reason: local context export to 'review-agent' is allowed by policy; surface 'review-agent' allows state areas summary, active_goal, relevant_artifacts, git_context, open_loops, recent_attempts and memory scopes working, episodic
