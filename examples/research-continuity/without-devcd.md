# Without DevCD

This is the baseline for a fresh research agent after the prior chat context is lost and no DevCD continuity packet is available.

## What The New Agent Knows

- The user was researching a complex topic.
- The repository contains a checked-in example, but the prior reasoning state is not in chat.

## What The New Agent Does Not Know

- The research goal was: `Assess whether retrieval latency changes answer quality in multi-source research agents`.
- The reviewed sources were `synthetic-paper-alpha` and `synthetic-report-beta`, and only metadata should be visible.
- The current hypothesis was: `Lower retrieval latency may improve answer quality only when source set size is controlled.`
- The failed approach was comparing latency outcomes without matching source set size.
- The next agent should not repeat that comparison until source set size is matched or explicitly controlled.
- Full research note text and private browser context were withheld by policy.
- The suggested next step was to review one synthetic source with matched source set size before updating the hypothesis.

## Likely Failure Mode

A careful agent would ask the user to reconstruct the research state. A rushed agent might repeat the same cross-source comparison and treat the failed hypothesis check as fresh work.

## What This Baseline Proves

Without a policy-filtered continuity packet, research continuity depends on chat history or manual user explanation. DevCD does not decide the research conclusion. It preserves the local, metadata-only state needed for the next agent to continue safely.
