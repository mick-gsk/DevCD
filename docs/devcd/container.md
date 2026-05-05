# Container Sandbox

DevCD's primary install path is local Python packaging, not hosted deployment.
The container image is a reproducible sandbox for demos, smoke tests, and MCP/API
experiments where an isolated filesystem is useful.

The image keeps runtime state under `/data`, runs as a non-root user, and exposes
only the DevCD local API port. Bind the host port to loopback unless you are
intentionally testing a broader network boundary.

## Build Locally

```bash
docker build -t devcd:local .
```

## Run The Daemon

```bash
docker run --rm \
  -p 127.0.0.1:8765:8765 \
  -v devcd-data:/data \
  devcd:local
```

DevCD writes the local bearer token to `/data/token` on startup when no token is
configured. To inspect the API from the host, read the token from the mounted
volume or set `DEVCD_API_TOKEN` explicitly when starting the container.

Example with an explicit local token:

```bash
docker run --rm \
  -e DEVCD_API_TOKEN=devcd-local-token \
  -p 127.0.0.1:8765:8765 \
  -v devcd-data:/data \
  devcd:local
```

Then query from the host:

```bash
curl -H "Authorization: Bearer devcd-local-token" http://127.0.0.1:8765/state
```

## CLI Smoke Tests

The container can also run one-shot CLI checks without starting the daemon:

```bash
docker run --rm devcd:local devcd --help
docker run --rm devcd:local devcd quickstart --no-tui --json --endpoint http://127.0.0.1:9/state
```

## Security Notes

- The container is a sandbox and CI artifact check, not the default trust model.
- Keep published ports bound to `127.0.0.1` for local use.
- Mount `/data` only when you intentionally want ledger and token persistence.
- Do not bake `.devcd/`, local ledgers, tokens, or private workspace files into
  the image.
- Remote export remains disabled by default.
- MCP remains read-only in the current MVP.
