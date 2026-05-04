# Changelog

All notable changes to DevCD will be documented in this file.

The project follows Conventional Commits and Semantic Versioning once public releases begin.

## 0.1.0 - Unreleased

Short version: Initial local-first context daemon foundation.

### Added

- Python monorepo scaffold with Vertical Slice Architecture.
- MVP daemon API for `POST /event`, `GET /state`, and `GET /memory/{scope}`.
- Default observe-only policy layer with explicit policy reasoning.
- Working-memory store with 5-minute TTL.
- Local JSON Lines event ledger.
- Initial state and event JSON Schemas.
- Runtime config via `devcd.toml` and `DEVCD_` environment variables.
- CLI commands for config initialization and event submission.
- Git snapshot source for branch and latest-commit events.
