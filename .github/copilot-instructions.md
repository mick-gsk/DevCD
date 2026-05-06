# DevCD Copilot Instructions

Canonical repository guidance now lives in `.github/instructions/copilot.instructions.md`.
Keep this file as a lightweight compatibility layer because DevCD tooling, docs,
and generated workspace setup still reference `.github/copilot-instructions.md`.

- Read `.github/instructions/copilot.instructions.md` for the full codebase patterns.
- Keep changes minimal, typed, and covered by focused tests.
- Prefer slice-owned models, services, API routes, and tests under `packages/devcd-core/src/devcd/slices/<slice_name>/`.
- Shared code belongs in `packages/devcd-core/src/devcd/kernel/` only when at least two slices need it.
- Preserve local-first privacy defaults: observe by default, deny actions by default, never introduce remote export without explicit policy.
- Every state-changing operation must be explainable through a policy decision.
- Run `make check` before considering implementation work complete.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read
`specs/002-ambient-context-kernel/plan.md`.
<!-- SPECKIT END -->
