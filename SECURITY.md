# Security policy

## Reporting a vulnerability

If you discover a security vulnerability in tolvi-solo, please **do not** open a public GitHub issue.

Instead, report it privately by [opening a security advisory](https://github.com/tolvi-labs/tolvi-solo/security/advisories/new) in this repository, or by emailing `security@tolvilabs.com`. We will acknowledge within 48 hours.

## Scope

The following are in scope:

- The installer (`install.sh`) and the plugin manifests
- The hooks it installs, which run inside your agent sessions
- Anything that sends vault content off your machine

The following are out of scope (please file them as regular issues):

- Theoretical vulnerabilities without a proof of concept
- Issues in third-party dependencies (please report them upstream)
- Issues in your own deployment or configuration

## Supported versions

| Version | Supported |
|---|---|
| pre-1.0 | Best-effort; security fixes land on `main` |

A formal supported-versions policy will be published when 1.0 ships.
