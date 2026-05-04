# DevCD Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
pre-commit install
make check
```

## Commands

| Command | Purpose |
| --- | --- |
| `make lint` | Ruff lint checks |
| `make format` | Ruff formatting and safe lint fixes |
| `make typecheck` | mypy over the core package |
| `make test` | pytest suite |
| `make check` | lint, typecheck, and tests |
| `make run` | run the local daemon on `127.0.0.1:8765` |

## Architecture

DevCD uses Vertical Slice Architecture. A slice owns the request/response models, domain service, and tests for one product capability.

Current slices:

| Slice | Purpose |
| --- | --- |
| `events` | normalized developer event contract and local ledger |
| `host_state_engine` | work-state tree, state update behavior, HTTP API |
| `memory_layer` | working, episodic, and semantic memory contracts |
| `policy_layer` | observation/action authorization decisions |

## Test Strategy

- Unit-test slice services directly.
- API-test route contracts through `fastapi.testclient.TestClient`.
- Add regression tests for every policy exception or sensitive-data rule.

## Privacy Rule

Local-first is the default. Any export, remote sync, or agent action must be opt-in and policy-gated.
