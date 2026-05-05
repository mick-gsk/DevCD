# Agent Switch Demo

This demo shows DevCD solving agent handoff, not only context reset. A
`coding-agent` produces local work context, a `review-agent` asks for a handoff,
and DevCD returns a surface-specific view with policy explanations for what was
included or withheld.

The fixture is local JSONL and uses the real CLI path:

```bash
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface coding-agent
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface review-agent
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface public-demo --json
```

PowerShell uses the same commands from the repository root.

## Scenario

1. `coding-agent` records work on the ambient context service, CLI tests, and
   the expected review-agent handoff artifact.
2. A first expected output is incomplete because it only covers the coding
   surface.
3. `review-agent` requests a handoff for review.
4. DevCD returns review-relevant files, Git metadata, visible attempts, and the
   latest failure while omitting coding-only blocker/suggestion lists.
5. Sensitive note and test-output payloads, plus disabled browser context, are
   withheld everywhere and represented only by safe summaries.

## Expected Outputs

- `expected-coding-agent-handoff.md`: the coding surface. It includes the full
  working context, blockers, suggested next steps, artifacts, Git metadata, and
  withheld-context explanations.
- `expected-review-agent-handoff.md`: the review surface. It preserves
  review-relevant artifacts, Git metadata, visible attempts, latest failure, and
  policy summary, while omitting blocker and suggestion state areas.

The outputs intentionally differ. The review handoff still tells the reviewer
what changed and what failed, but it does not expose every coding-agent work
queue field. The `public-demo` surface is not checked in as a Markdown fixture
because it is intentionally sparse; tests assert that it removes goal, artifacts,
Git branch, blockers, and failure details while keeping policy-safe withheld
summaries.

## Rebuild

```bash
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface coding-agent
devcd context handoff-demo --events examples/agent-switch/sample-events.jsonl --surface review-agent
```

Compare the outputs with the checked-in expected files. The synthetic sensitive
note, test-output log, and private browser URL from the fixture must not appear
in any handoff.