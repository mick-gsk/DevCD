# Context Brief Demo

This demo shows the smallest DevCD loop: record local work context, then ask for a
policy-filtered brief that a coding agent can consume.

## Setup

Install DevCD from this repository and start the daemon:

```bash
python -m pip install -e ".[dev]"
devcd init
devcd run
```

CLI commands automatically read the local bearer token from `DEVCD_TOKEN` or `.devcd/token`
for loopback API calls. You only need to read it manually for direct HTTP requests:

```bash
TOKEN="$(cat .devcd/token)"
```

PowerShell:

```powershell
$env:DEVCD_TOKEN = Get-Content .devcd/token
```

## Record Context

```bash
devcd event task goal_update --payload '{"current_goal":"Add a token-aware DevCD quickstart"}'
devcd event ide file_focus --payload '{"path":"README.md","duration_seconds":45}'
devcd event git branch_change --payload '{"branch":"main"}'
```

PowerShell:

```powershell
devcd event task goal_update --payload '{"current_goal":"Add a token-aware DevCD quickstart"}'
devcd event ide file_focus --payload '{"path":"README.md","duration_seconds":45}'
devcd event git branch_change --payload '{"branch":"main"}'
```

## Ask for the Brief

```bash
devcd context brief --surface cli --detail standard
```

The response includes the active intent, relevant artifact, recent attempts,
suggested next steps, and policy decision. This is the handoff DevCD is designed
for: agents can ask the local daemon what matters instead of asking you to
re-explain the workspace.
