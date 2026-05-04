---
name: commit-push
description: "Repository-safe commit and push workflow for DevCD. Use when preparing commits, choosing conventional commit messages, running validation, or deciding whether a push is allowed. Keywords: commit, push, git push, conventional commit, changelog, validation."
argument-hint: "Describe what changed and whether you need commit help, push readiness, or both."
---

# Commit And Push Skill

Use this skill for repository-safe commit and push workflows in DevCD.

## When To Use

- Prepare a commit after code changes
- Choose the correct conventional commit type
- Check whether a push is allowed
- Run validation gates before pushing

## Core Rules

1. **Do not push autonomously.** A push requires explicit maintainer approval.
2. **Use conventional commits.** Release automation depends on `feat:`, `fix:`, and `BREAKING:` semantics.
3. **Run validation before every push.** The standard gate is `make check`.
4. **Do not bypass hooks without justification.** Environment-variable bypasses are emergency-only.

## Step 1: Classify The Change

Choose the commit type from the actual impact:

- `fix:` for bug fixes and regressions
- `feat:` for new user-visible capabilities
- `refactor:` for internal restructuring without behavior change
- `docs:` for documentation-only changes
- `test:` for tests-only changes
- `chore:` for maintenance work
- `BREAKING:` or a `BREAKING CHANGE:` footer for incompatible changes

**Scope convention:** Use the slice name as the scope when applicable:
```
feat(memory_layer): add TTL-aware working memory
fix(policy_layer): deny mutations when policy is unconfigured
test(events): cover ledger append edge cases
```

If the change touches API contracts, memory schemas, or policy rules, check whether an ADR under `docs/decisions/` is required before implementation. Stop and satisfy that requirement before committing.

## Step 2: Inspect The Working Tree

Review exactly what will be committed:

```bash
git status --short
git diff --stat
git diff
```

Check for unrelated files and leave them out of the commit.

## Step 3: Satisfy Change-Coupled Requirements

Before committing, verify these gates:

- **`feat:` commit planned:**
  - Include tests in the same diff
  - `make check` must pass
- **`feat:` or `fix:` commit planned:**
  - Include a `CHANGELOG.md` update
- **New public function in `src/devcd/`:**
  - Add a type annotation in the same diff (mypy strict mode is enforced)
- **API route added or changed:**
  - Update `specs/001-devcd-context-daemon/contracts/openapi.yaml` if applicable
- **`pyproject.toml` changed:**
  - Ensure lock file is updated too (if using uv or pip-compile)

## Step 4: Run Validation

Before push, the repository standard is:

```bash
make check
```

This runs: ruff lint → mypy strict typecheck → pytest suite.

For fast feedback during development, run targeted checks:

```bash
pytest tests/test_<slice>.py -v   # single slice
mypy packages/devcd-core/src      # typecheck only
ruff check .                       # lint only
```

Use exactly one full `make check` run per push cycle.

## Step 5: Create The Commit

Stage only the intended files:

```bash
git add <paths>
git commit -m "feat(slice): concise summary"
```

Good commit subjects are:
- specific
- outcome-oriented
- scoped to one logical change

Examples:

```text
fix(policy_layer): deny mutations when no policy is configured
feat(memory_layer): add TTL-aware working memory with eviction
test(events): cover ledger append with duplicate event IDs
docs: add ADR-002 for memory schema design
```

If the commit implements an ADR, add the decision trailer to the commit body:

```text
feat(host_state_engine): add state diff endpoint

Decision: ADR-002
```

## Step 6: Evaluate Push Readiness

Before any push, confirm all of the following:

- explicit maintainer approval to push exists
- no unrelated files are included
- `make check` is green for this push cycle
- the branch and target are intentional

Useful checks:

```bash
git diff --name-only origin/main HEAD
git log --oneline origin/main..HEAD
```

## Step 7: Push Only With Approval

If and only if approval exists:

```bash
git push origin main
```

Do not use `--no-verify` unless the maintainer explicitly requests an emergency override and the reason is documented.

## Review Checklist

- [ ] Commit type matches actual change impact
- [ ] Scope reflects the affected slice or component
- [ ] Only intended files are staged
- [ ] Change-coupled requirements are satisfied (tests, CHANGELOG, type annotations)
- [ ] `make check` is green
- [ ] Push approval was explicitly granted before pushing
