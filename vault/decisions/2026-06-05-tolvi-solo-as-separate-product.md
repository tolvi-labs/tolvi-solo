---
tags: [decision, tolvi-solo]
date: 2026-06-05
repo: tolvi-solo
status: active
ticket: none
user_impact: none
product_area: Distribution
---

# tolvi-solo as a separate product repo, not a subset of tolvi

**Date:** 2026-06-05
**Repo:** tolvi-solo

## Why
Solo engineers managing many repos want vault benefits without the full Tolvi stack (no server, no SDK, no pgvector). Packaging this as a separate product rather than a slim branch of the main repo allows it to have its own identity, release cadence, schema library, and eventual marketing page with role-based verticals (Engineer, Writer, CPA, Entrepreneur).

## How
- Created `tolvi-labs/tolvi-solo` as a private-then-public repo, separate from `tolvi-labs/tolvi`.
- Core deliverable is a **schema library** (role-specific templates in `packs/<name>/templates/`) plus a **shell installer** (`install.sh`) that provisions `vault/` in any git repo and optionally wires Claude Code hooks.
- Format compatibility maintained: all templates use `tolvi-format-v1` frontmatter so vaults provisioned by tolvi-solo work identically with the `tolvi` CLI and with the sync-session / recall skills.
- Engineer pack ships first; Writer, Entrepreneur, CPA are placeholders in the README packs table.
- Rejected: embedding solo configs inside the tolvi monorepo as `integrations/solo/` — that would make it harder to give the product its own identity, docs page, and release lifecycle.
- Rejected: a trimmed fork of the tolvi Go CLI — the schema packs and installer add value without requiring users to install a compiled binary.

## Outcome
tolvi-solo is a live public repo at `github.com/tolvi-labs/tolvi-solo` with the Engineer pack, shell installer, Claude Code hooks, and Apache 2.0 license.
