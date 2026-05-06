# Publishing

DevCD is not automatically published to PyPI yet. The repository contains the
release machinery needed for a safe alpha, but external publication should only
be enabled after project ownership and Trusted Publishing are configured.

This page is the maintainer runbook for the first public package release.

## Public Install Story

The first normal-consumption milestone is narrow on purpose:

- `pip install devcd`
- `pipx install devcd`
- optional `uvx devcd --help` guidance when that path is verified

Until that package exists on PyPI, the repository should describe checkout
installs as a temporary evaluation path, not as the final public story.

After publication, the primary public path should collapse to:

```bash
pip install devcd
devcd onboard
devcd agentic action-packet
```

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

## Maintainer Runbook

Use this order for the first real publish. Do not skip the clean-environment
install proof after upload.

### 1. Confirm package ownership and index setup

Before touching GitHub Actions:

1. Confirm that the `devcd` project name on PyPI is available or already owned.
2. Enable 2FA on both PyPI and TestPyPI maintainer accounts.
3. Create the `devcd` project on TestPyPI first if it does not exist yet.
4. Configure Trusted Publishing for this repository on both indexes.

Use these values when creating the Trusted Publisher entry:

- Owner: `mick-gsk`
- Repository: `DevCD`
- Production workflow: `.github/workflows/publish-pypi.yml`
- Test workflow: `.github/workflows/publish-test-pypi.yml`

### 2. Cut a release candidate from a clean repo state

Run these commands from the repository root:

```bash
git status -sb
make check
python -m mkdocs build --strict --site-dir /tmp/devcd-mkdocs-check
make distribution
```

On PowerShell, use:

```powershell
git status -sb
make check
python -m mkdocs build --strict --site-dir "$env:TEMP\devcd-mkdocs-check"
make distribution
```

The release candidate should not proceed until all three gates pass.

### 3. Publish to TestPyPI first

Create and push a release-candidate tag, for example:

```bash
git tag v0.2.0rc1
git push origin v0.2.0rc1
```

Then run the `Publish TestPyPI` workflow and pass the exact ref, for example
`v0.2.0rc1`.

After the workflow succeeds, verify installation in a clean environment.

Bash:

```bash
python -m venv .tmp-testpypi
. .tmp-testpypi/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple devcd
devcd smoke
devcd onboard --help
deactivate
```

PowerShell:

```powershell
python -m venv .tmp-testpypi
.\.tmp-testpypi\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple devcd
devcd smoke
devcd onboard --help
deactivate
```

If TestPyPI install or smoke fails, fix the release candidate and rerun TestPyPI
before touching production PyPI.

## GitHub Release

Pushing a semantic version tag such as `v0.2.0` runs the release workflow:

```bash
git tag v0.2.0
git push origin v0.2.0
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
5. Trigger the `Publish PyPI` workflow with the exact tag ref, for example `v0.2.0`.

Recommended production sequence:

1. Merge the final release commit to the default branch.
2. Update `CHANGELOG.md` so the target version section is the newest visible release block.
3. Create and push the final tag, for example `v0.2.0`.
4. Run the `Publish PyPI` workflow for that exact ref.
5. Wait for the workflow to complete successfully before changing README install instructions.

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

For the first release, also verify the primary first-run path explicitly:

```bash
devcd onboard
devcd agentic action-packet
```

On Windows PowerShell, the same post-release proof is:

```powershell
python -m venv .tmp-pypi
.\.tmp-pypi\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install devcd
devcd smoke
devcd onboard
devcd agentic action-packet
deactivate
```

Only after this proof passes should README and Getting Started switch the
dominant install path from checkout install to `pip install devcd`.

## Container Image

The Dockerfile is a sandbox and CI smoke-test path, not DevCD's primary trust
model. Build and run details are documented in the container sandbox guide.

A public container registry workflow should only be added after the local Docker
sandbox and GitHub Actions build have passed on the default branch.
