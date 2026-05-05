# Without DevCD

This is not a simulated LLM transcript. It is the honest baseline for a fresh
agent when the only prompt is something like "continue the previous work" and
no DevCD handoff packet is provided.

## What The New Agent Knows

- There is some repository state in the checkout.
- The user wants work to continue.

## What The New Agent Does Not Know

- The current goal was: `Finish the before/after continuity proof demo for DevCD`.
- The latest visible failure was: `make check still fails: expected CLI output is stale and omits do_not_repeat`.
- The prior attempted fix was: `Added a generic handoff paragraph but did not regenerate the CLI output from the fixture`.
- The attempt not to repeat is: `Do not repeat the last attempted fix unchanged`.
- The next action should be: `Regenerate with-devcd.md from sample-events.jsonl and verify withheld_context is present`.
- Sensitive note content and disabled browser context should remain hidden.

## Likely Failure Mode

A careful agent would need to rediscover the goal and failure history by asking
the user or searching the repository. A rushed agent might repeat the stale
generic handoff paragraph because it cannot see that this exact attempt already
failed.

## What This Baseline Proves

Without a policy-filtered handoff packet, continuity depends on chat history or
manual user explanation. DevCD does not fix the code. It provides local,
policy-filtered context so the next agent can start from the right state.