# Publishing

DevCD is not automatically published to PyPI yet. The repository contains the
release machinery needed for a safe alpha, but external publication should only
be enabled after project ownership and Trusted Publishing are configured.

## Public Install Story

The first normal-consumption milestone is narrow on purpose:

- `pip install devcd`
- `pipx install devcd`
- optional `uvx devcd --help` guidance when that path is verified

Until that package exists on PyPI, the repository should describe checkout
installs as a temporary evaluation path, not as the final public story.

## Local Distribution Gate

Build and validate release artifacts locally:

```bash
make distribution
```

For a user-facing sanity check after installation from a checkout or public
artifact:

```bash
devcd smoke
```

For the repo-root maintainer shortcut that runs the same install-proof script:

```bash
make smoke
```

The gate builds the source distribution and wheel, runs `twine check`, verifies
that the wheel contains the typed package marker, rejects repository-only files
such as tests/docs/site output, installs the wheel into a temporary virtual
environment, and smoke-tests the installed CLI.

The installed-wheel smoke test includes:

```bash
devcd --help
devcd context packs --json
devcd quickstart --no-tui --json
```

## GitHub Release

Pushing a semantic version tag such as `v0.1.0` runs the release workflow:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The release workflow runs checks, builds artifacts, verifies metadata,
smoke-tests the wheel, and attaches the artifacts to a GitHub Release.

GitHub Releases should be treated as the public evidence page for each version:
artifact files, changelog section, and verification notes should all agree with
the install commands shown in the README.

## PyPI Publishing

PyPI publication is manual and OIDC-based through `.github/workflows/publish-pypi.yml`.
It does not require a long-lived PyPI token in GitHub Secrets.

Before running it:

1. Create or claim the `devcd` PyPI project.
2. Configure PyPI Trusted Publishing for this GitHub repository and workflow.
3. Confirm the version in `pyproject.toml` matches the intended release tag.
4. Run the local `make distribution` gate.
5. Trigger the `Publish PyPI` workflow with the exact tag ref, for example `v0.1.0`.

The workflow checks out the requested ref, installs dev dependencies, runs
`make check`, runs `make distribution`, and publishes the verified artifacts to
PyPI using PyPI's trusted publisher exchange.

After the first public package release, verify the public consumption path in a
clean environment exactly as users will run it:

```bash
pip install devcd
devcd smoke
```

Also verify the isolated CLI path:

```bash
pipx install devcd
devcd smoke
```

## Container Image

The Dockerfile is a sandbox and CI smoke-test path, not DevCD's primary trust
model. Build and run details are documented in the container sandbox guide.

A public container registry workflow should only be added after the local Docker
sandbox and GitHub Actions build have passed on the default branch.
