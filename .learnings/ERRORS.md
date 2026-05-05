# Errors

## [ERR-20260505-003] make_check

**Logged**: 2026-05-05T00:00:00Z
**Priority**: low
**Status**: resolved
**Area**: service

### Summary
`make check` failed on mypy after Ruff passed for the Research Pack change.

### Error
`service.py:1671: error: Returning Any from function declared to return "Literal['unknown', 'success', 'failure', 'interrupted']"`

### Context
- Command: `make check`
- Related file: `packages/devcd-core/src/devcd/slices/ambient_context/service.py`

### Suggested Fix
Return explicit literal branches from `_research_attempt_outcome` instead of returning the `Any` value from `_payload_value` after a membership check.

### Resolution
- **Resolved**: 2026-05-05T00:00:00Z
- **Notes**: Replaced the membership return with explicit `success`, `failure`, `interrupted`, and `unknown` branches; mypy then passed.

### Metadata
- Reproducible: yes
- Related Files: packages/devcd-core/src/devcd/slices/ambient_context/service.py

---

## [ERR-20260505-002] make_check

**Logged**: 2026-05-05T00:00:00Z
**Priority**: low
**Status**: resolved
**Area**: service

### Summary
`make check` failed on Ruff after adding Research Pack continuity rendering.

### Error
Ruff reported import ordering in `packages/devcd-core/src/devcd/cli.py` and E501 line-length errors in `packages/devcd-core/src/devcd/slices/ambient_context/service.py` and `tests/test_cli.py`.

### Context
- Command: `make check`
- Related files: `packages/devcd-core/src/devcd/cli.py`, `packages/devcd-core/src/devcd/slices/ambient_context/service.py`, `tests/test_cli.py`

### Suggested Fix
Run import sorting or reorder imports, then wrap long tuple literals, comprehensions, and assertion strings before rerunning `make check`.

### Resolution
- **Resolved**: 2026-05-05T00:00:00Z
- **Notes**: Wrapped the Research Pack service/test lines and let Ruff fix the CLI import ordering.

### Metadata
- Reproducible: yes
- Related Files: packages/devcd-core/src/devcd/cli.py, packages/devcd-core/src/devcd/slices/ambient_context/service.py, tests/test_cli.py

---

## [ERR-20260505-001] make_check

**Logged**: 2026-05-05T00:00:00Z
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
`make check` failed on Ruff after adding a long assertion to the secure resurrection CLI test.

### Error
Ruff reported line-length errors in `tests/test_cli.py` around the suggested next action and category assertions.

### Context
- Command: `make check`
- Related file: `tests/test_cli.py`

### Suggested Fix
Wrap long assertion values immediately when adding contract-heavy tests.

### Resolution
- **Resolved**: 2026-05-05T00:00:00Z
- **Notes**: Split the long assertions across multiple lines before rerunning verification.

### Metadata
- Reproducible: yes
- Related Files: tests/test_cli.py

---

## [ERR-20260504-001] pytest_mcp_server

**Logged**: 2026-05-04T00:00:00Z
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
Targeted MCP pytest run failed during collection because `TextIO` was imported from `collections.abc`.

### Error
`ImportError: cannot import name 'TextIO' from 'collections.abc'`

### Context
- Command: `python -m pytest tests/test_mcp_server.py tests/test_cli.py::test_cli_exposes_mcp_serve_command -v`
- Related file: `packages/devcd-core/src/devcd/slices/mcp_server/service.py`

### Suggested Fix
Import `TextIO` from `typing` when annotating text streams.

### Resolution
- **Resolved**: 2026-05-04T00:00:00Z
- **Notes**: Updated the MCP service import to `from typing import Any, TextIO`.

### Metadata
- Reproducible: yes
- Related Files: packages/devcd-core/src/devcd/slices/mcp_server/service.py

---

## [ERR-20260504-003] make_check

**Logged**: 2026-05-04T12:00:00Z
**Priority**: low
**Status**: resolved
**Area**: service

### Summary
`make check` failed on Ruff E501 after adding the agent limitations field.

### Error
`packages/devcd-core/src/devcd/slices/ambient_context/service.py:207:101 E501 Line too long (102 > 100)`

### Context
- Command: `make check`
- Related file: `packages/devcd-core/src/devcd/slices/ambient_context/service.py`

### Suggested Fix
Split ternary expressions across multiple lines before running the full check.

### Resolution
- **Resolved**: 2026-05-04T12:00:00Z
- **Notes**: Wrapped the `git_context` expression before rerunning verification.

### Metadata
- Reproducible: yes
- Related Files: packages/devcd-core/src/devcd/slices/ambient_context/service.py

---

## [ERR-20260504-002] make_check

**Logged**: 2026-05-04T00:00:00Z
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
`make check` failed on Ruff after adding the MCP slice.

### Error
Ruff reported an unsorted import block in `cli.py` and an E501 line-length error in `mcp_server/service.py`.

### Context
- Command: `make check`
- Related files: `packages/devcd-core/src/devcd/cli.py`, `packages/devcd-core/src/devcd/slices/mcp_server/service.py`

### Suggested Fix
Keep new slice imports alphabetized and split JSON-RPC error dictionaries across lines when they approach the 100-character limit.

### Resolution
- **Resolved**: 2026-05-04T00:00:00Z
- **Notes**: Reordered the MCP import before memory_layer and wrapped the long error response.

### Metadata
- Reproducible: yes
- Related Files: packages/devcd-core/src/devcd/cli.py, packages/devcd-core/src/devcd/slices/mcp_server/service.py

---
