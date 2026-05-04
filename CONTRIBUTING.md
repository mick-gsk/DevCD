# Contributing

DevCD is early-stage. Contributions should keep the local-first privacy model and Vertical Slice Architecture intact.

## Getting Started

```bash
git clone https://github.com/mick-gsk/DevCD.git
cd DevCD
python -m pip install -e ".[dev]"
pre-commit install
devcd init
make check       # verify everything passes before you start
```

Requirements: Python 3.11+, pip.

## Workflow

1. Open or pick an issue with a clear slice label.
2. Keep changes focused on one feature slice unless the issue explicitly spans slices.
3. Add or update tests next to the behavior being changed.
4. Run `make check` before opening a pull request.
5. Fill in the PR template and link the related issue.

## Commit Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(host-state-engine): add state snapshot endpoint
fix(policy-layer): deny sensitive note events by default
docs(memory): clarify working-memory TTL
test(events): cover ledger rotation edge case
chore: update pre-commit hooks
```

## Architecture Rules

- Add feature behavior under `packages/devcd-core/src/devcd/slices/<slice>/`.
- Keep `devcd/kernel/` small and shared only by proven need.
- Do not add outbound network behavior unless policy, docs, and tests make the opt-in boundary explicit.
- Every state-changing operation must return or record policy reasoning.
- Full type annotations required. `mypy` must pass in strict mode.

## Good First Issues

Issues labelled [`good first issue`](https://github.com/mick-gsk/DevCD/labels/good%20first%20issue) are small, self-contained, and well-specified. They are a good starting point if you are new to the codebase.

## Opening an Issue

Use the issue templates for [bug reports](.github/ISSUE_TEMPLATE/bug_report.yml) and [feature requests](.github/ISSUE_TEMPLATE/feature_request.yml). For design questions or general ideas, use [Discussions](https://github.com/mick-gsk/DevCD/discussions) instead.

## Code Style

- `ruff` for linting and formatting (`line-length = 100`)
- `mypy` strict mode for `packages/devcd-core/src`
- No bare `except`, no `# type: ignore` without a comment explaining why
- Pydantic v2 for all data models

## Running Tests

```bash
pytest tests -q              # full suite
pytest tests/test_api.py -q  # single file
```

## Maintainer

DevCD is maintained by [Mick Gottschalk](https://github.com/mick-gsk). Community contributions are welcome and encouraged.
