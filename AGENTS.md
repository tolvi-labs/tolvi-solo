# AGENTS.md

Guidance for coding agents working in this repo. Humans: see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## What this is

A vault for solo builders: the Tolvi format with no server and no binary to install. A shell installer plus role-specific template packs.

## Build and test

```bash
bash scripts/check-conventions.sh        # the whole suite
python3 scripts/check-vault-meta.py vault/.vault-meta.json
```

`check-conventions.sh` provisions a real vault into a temp repo and validates what the installer wrote. That is deliberate: asserting on the installer's heredoc text passes while the vault it makes stays unreadable, which is exactly how a non-conformant meta shipped for the life of this repo.

## Conventions

- **The slash commands are downstream.** `commands/tolvi-*.md` are synced byte-for-byte from `tolvi/skills/tolvi/commands/`. A change belongs there first and is copied here, never authored in both places.
- **Duplication that cannot be shared is pinned by a check.** A standalone clone cannot depend on a sibling repo, so the remediation text and the conventions script are deliberate copies of tolvi's. `check-conventions.sh` holds them in step.
- **Vault metadata is `tolvi-format-v2`.** Solo's own fields ride in the `x-` namespace the format reserves, because the published schema sets `additionalProperties: false`.
- **Write for bash 3.2.** macOS ships it. A heredoc inside a command substitution is unparseable there, which is why the meta validator is its own file.

## What not to do

- Do not let `install.sh` write a meta the `tolvi` CLI cannot read. The conformance check exists because that shipped once already.
