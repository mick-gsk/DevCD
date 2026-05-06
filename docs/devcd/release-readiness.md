# Release Readiness

DevCD is pre-alpha. This page makes the current maturity level visible so users
can evaluate the project without guessing from repository shape alone.

The release goal for the first public alpha is not to look production-sized. It
is to make the first continuity proof installable, inspectable, policy-safe, and
easy to share.

The first public proof is not “the whole platform works.” The first public proof
is narrower and more important: a fresh agent can read a useful Action Packet in
minutes, without remote services or recap-heavy setup.

## What Works Today

- Checkout install from this repository works.
- `devcd onboard` prepares a local workspace without starting the daemon.
- `devcd handoff` and `devcd capture` can seed metadata-only continuity.
- `devcd agentic action-packet` gives the next agent a first handoff surface.
- `devcd quickstart` and `devcd context passport` provide the broader follow-up view.
- `devcd smoke`, `make check`, and `make distribution` provide local verification paths.

## What Still Blocks Normal Consumption

- PyPI ownership and Trusted Publishing still need maintainer setup outside the repo.
- No public package release exists yet, so README and docs must not over-claim `pip install devcd`.
- Secondary channels such as Homebrew and a public container registry are still follow-on work, not the alpha blocker.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Package metadata | Present | `pyproject.toml` defines the `devcd` package and CLI entry point. |
| Typed package marker | Present | The wheel includes `devcd/py.typed` to match the typed classifier. |
| Distribution check | Present | `make distribution` builds, checks metadata, verifies wheel contents, and smoke-tests the installed CLI. |
| PyPI publishing | Prepared | Manual OIDC workflow exists, but publication remains blocked until PyPI Trusted Publishing is configured. |
| Container sandbox | Present | Dockerfile and CI container workflow build and smoke-test an isolated local sandbox image. |
| Public package release | Not published | PyPI, pipx, uvx, and Homebrew instructions should wait until a release exists. |
| Local install path | Present | Checkout install from source is documented today. |
| Local-first defaults | Present | Loopback, local storage, deny actions, and no remote export are the default posture. |
| Core continuity demo | Present | Action Packet and continuity fixtures are documented. |
| Extension surface | Present | Context Packs and event recipes provide the current metadata-only extension path. |
| Agent-ready setup | Present | `devcd onboard` prepares local config, selected workspace instruction files, and the Action Packet workflow without external config mutation. |
| MCP integration | Present | Read-only local MCP resources and smoke-test commands are documented. |
| OpenClaw integration | Present | Local DevCD MCP shape and snippet are verified; full OpenClaw gateway E2E remains explicitly unclaimed. |
| Security policy | Present | Security defaults, data classes, and threat model are documented. |
| Changelog discipline | Present | `CHANGELOG.md` tracks unreleased `0.1.0` changes. |
| Hosted deployment | Not planned for alpha | DevCD handles local developer context; cloud deployment is not the primary trust model. |

## Alpha Bar

The first public alpha should be considered ready when all of these are true:

- `pip install devcd` works from PyPI.
- `pipx install devcd` works for CLI-first users.
- `uvx devcd --help` or equivalent uv guidance is documented if supported.
- `devcd onboard` gives a useful first-run path without requiring a running daemon.
- `devcd handoff` or equivalent metadata capture gives the next agent a useful
  warm-start packet without raw recap text.
- `devcd init` creates local configuration without surprising side effects.
- `devcd smoke` validates the installed CLI without requiring a running daemon.
- `devcd quickstart` gives a useful local-first activation report.
- `devcd agentic action-packet` renders a useful first handoff from the
  configured local ledger.
- `devcd context passport` renders the broader continuity view from the
  configured local ledger.
- `devcd integrations openclaw --smoke-test` verifies the read-only MCP shape
  without installing or mutating OpenClaw.
- `make check` passes on the release commit.
- `make distribution` passes on the release commit.
- `mkdocs build --strict` passes on the release commit.
- `SECURITY.md` documents the current data classes, defaults, and reporting path.
- `CHANGELOG.md` has a dated release section with user-visible changes.
- Known limitations are documented rather than hidden.

## Distribution Strategy

DevCD should optimize for local installation before hosted deployment.

Recommended order:

1. PyPI package release for `pip install devcd`.
2. pipx guidance for isolated CLI installs.
3. uv guidance for fast one-shot local trials.
4. GitHub Releases with changelog, source archive, and verification notes.
5. Homebrew tap only after the CLI surface stabilizes.
6. Docker as a demo or sandbox path, not as the primary user path.

Fly.io, Render, or other hosted deployment artifacts are not the first alpha
priority because DevCD's product boundary is local developer context. The
container image is framed as a local sandbox and CI smoke-test surface, not as
the default operating mode.

## Trust Signals To Keep Current

- README first viewport: one clear value proposition and one short proof path.
- Getting started: one dominant first-run path ending at Action Packet.
- `SECURITY.md`: concrete defaults, data classes, threat model, and reporting.
- `CHANGELOG.md`: dated releases once public releases begin.
- CI badge: green on the default branch.
- Documentation site: strict MkDocs build passes.
- Examples: checked-in fixture outputs match current schemas.
- Extension docs: Context Packs and recipes stay metadata-only and policy-gated.
- Policy docs: every state-changing operation remains policy-explainable.

## Known Pre-Alpha Limitations

- No public PyPI release yet; the publish workflow requires PyPI Trusted Publishing setup first.
- No stable versioned API guarantee yet.
- No VS Code extension or native IDE event source yet.
- No Homebrew tap.
- No production support window.
- No remote sync or remote export by default.
- No write-capable MCP tools.
- No hosted deployment story by design for the first alpha.

These are maturity constraints, not contradictions to the core proof. The local
warm-start workflow is already the thing being validated.

## Release Checklist

Before cutting a public alpha release:

```bash
make check
python -m mkdocs build --strict --site-dir "$TEMP/devcd-mkdocs-check"
make distribution
```

After publication, prove the public install path in a clean environment with:

```bash
pip install devcd
devcd smoke
```

On PowerShell, replace the MkDocs site directory with a valid temporary path,
for example:

```powershell
python -m mkdocs build --strict --site-dir "$env:TEMP\devcd-mkdocs-check"
```

The build artifacts should be inspected before upload. Do not publish a package
that claims support for install paths that have not been verified locally.
