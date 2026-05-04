# DevCD Copilot Instructions

This repository is a local-first Developer Context Daemon built as a Python monorepo with Vertical Slice Architecture.

- Keep changes minimal, typed, and covered by focused tests.
- Prefer slice-owned models, API routes, services, and tests under `devcd/slices/<slice_name>/`.
- Shared code belongs in `devcd/kernel/` only when at least two slices need it.
- Preserve local-first privacy defaults: observe by default, deny actions by default, never introduce remote export without explicit policy.
- Every state-changing operation must be explainable through a policy decision.
- Run `make check` before considering implementation work complete.
<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
