# OpenClaw Product Benchmark Notes

Date: 2026-05-06

## Scope

This benchmark looked at OpenClaw as a product experience, not as a feature-by-feature clone target. The comparison focused on installation, first run, onboarding, diagnostics, and trust cues that make a developer tool feel polished.

## What Was Tried

- Cloned `https://github.com/openclaw/openclaw.git` into a temporary checkout.
- Read the OpenClaw README, package metadata, launcher, install docs, getting-started guide, onboarding docs, and CLI references.
- Ran the source launcher with `node openclaw.mjs --help`.
- Ran the published package with `npm exec --yes openclaw@latest -- --help`.
- Ran `npm exec --yes openclaw@latest -- onboard --help`.
- Ran isolated non-interactive onboarding with temporary `OPENCLAW_STATE_DIR` and `OPENCLAW_CONFIG_PATH`.
- Ran isolated `openclaw doctor --non-interactive` against that temporary state.
- Compared DevCD with `devcd --help`, `devcd onboard --help`, `devcd smoke --json`, `devcd doctor --json`, and `devcd onboard --preview --no-tui`.

## Observations

- OpenClaw's published package path is excellent: `npm exec --yes openclaw@latest -- --help` works immediately and prints version, command map, examples, and docs.
- OpenClaw's source checkout failure is also useful: it explains that `dist/entry.(m)js` is missing, gives `pnpm install && pnpm build`, and recommends installing the built package for releases.
- OpenClaw's getting-started path is a concrete success chain: install, onboard, verify gateway status, open dashboard, send the first message.
- OpenClaw's onboarding is very powerful but can overwhelm: the help output exposes many providers and flags at once.
- OpenClaw's failed non-interactive onboarding still classifies the failure, prints the target URL, and gives exact remediation commands.
- OpenClaw's successful `--skip-health` onboarding prints state writes, workspace status, gateway defaults, and JSON.
- OpenClaw Doctor feels product-grade because it names each subsystem, explains why it matters, and offers exact repair commands.
- OpenClaw Doctor also has rough edges: on Windows it emitted symlink errors and attempted completion repair during a non-interactive diagnostic run.
- DevCD already has a quieter local-first proof: `devcd smoke --json` is daemonless, deterministic, and does not require credentials.
- DevCD's weakest product gap is not capability; it is first-run guidance. The user needs one obvious command that explains what will happen, what success looks like, and what to run next.
- DevCD's `onboard --preview` is close, but showing `Agent-ready workspace - skipped` above an Agent-Layer proposal feels contradictory.

## Improvement Checklist

- [x] Add a zero-write `devcd welcome` command that acts as the product front door.
- [x] Make `devcd welcome --json` usable by automation and docs tests.
- [x] Update top-level help so new users start with `devcd welcome`, then `devcd onboard --preview`.
- [x] Make `devcd smoke` end with the next onboarding command, not just pass/fail checks.
- [x] Remove the confusing `Agent-ready workspace - skipped` line from preview flows that already show an Agent-Layer proposal.
- [x] Document the benchmark and connect it to the install/getting-started path.
- [x] Verify with focused CLI tests, docs build, and `make check`.

## Product Principle

DevCD should beat OpenClaw on the local-first continuity use case by being calmer, safer, and faster to prove: one install check, one preview, one explicit apply, one Action Packet. It should borrow OpenClaw's concrete success chain and diagnostics without copying its gateway breadth or noisy side effects.