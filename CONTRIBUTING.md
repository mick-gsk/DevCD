# Contributing

DevCD is early-stage. Contributions should keep the local-first privacy model and Vertical Slice Architecture intact.

## Workflow

1. Open or pick an issue with a clear slice label.
2. Keep changes focused on one feature slice unless the issue explicitly spans slices.
3. Add or update tests next to the behavior being changed.
4. Run `make check` before opening a pull request.

## Commit Format

Use Conventional Commits:

```text
feat(host-state-engine): add state snapshot endpoint
fix(policy-layer): deny sensitive note events by default
docs(memory): clarify working-memory TTL
```

## Architecture Rules

- Add feature behavior under `packages/devcd-core/src/devcd/slices/<slice>/`.
- Keep `devcd/kernel/` small and shared only by proven need.
- Do not add outbound network behavior unless policy, docs, and tests make the opt-in boundary explicit.
- Every state-changing operation must return or record policy reasoning.
