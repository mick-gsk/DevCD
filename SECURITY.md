# Security Policy

DevCD is a local context daemon and may process sensitive developer context. Treat privacy and local data boundaries as core product behavior.

## Supported Versions

No stable public release exists yet. Security fixes currently target the unreleased `0.1.x` line.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately to the maintainer instead of opening a public issue. Include the affected data class, reproduction steps, and whether local files, network export, or action policy was involved.

## Security Defaults

- Local storage only by default.
- Sensitive events are denied by the default policy.
- Actions are denied by the default policy.
- Remote export requires explicit future configuration and tests.
- Policy reasoning must be available for every accepted observation or action.
