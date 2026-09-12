---
tags: [decision, tolvi-solo]
date: 2026-09-12
repo: tolvi-solo
status: active
ticket: none
user_impact: low
product_area: Install / conventions
---

# The installer's CLI remediation and preflight block are deliberate duplicates of tolvi's

**Date:** 2026-09-12
**Repo:** tolvi-solo

## Why
`tolvi-solo` and `tolvi` now carry the same two pieces of text: the remediation printed when the `tolvi` binary is not on `PATH`, and the preflight block every slash command includes. Sharing them was the first instinct and does not survive contact with what this repo is. `tolvi-solo` is cloned on its own by people who never touch the `tolvi` repo, so a shared file would mean either a network fetch during install or a dependency on a checkout that is usually absent. Both are worse than copying about fifteen lines.

Duplication is still duplication, and the marketing site spent this same day proving where it leads: four hand-maintained copies of one stack section had drifted into four different answers about what the product is. The difference is not that the duplication here is acceptable in principle, but that it is pinned rather than trusted.

## How
- `scripts/check-conventions.sh` asserts both rules on every run: `install.sh` may never mention `go install` without also naming the `PATH` export, and no command's `PREFLIGHT` block may differ from `commands/_preflight.md`.
- The `tolvi` repo carries its own equivalents in `.github/scripts/`. Each repo pins its own copy, so neither depends on the other being present.
- Both copies carry a comment naming the other, so whoever edits one knows a sibling exists.

## Outcome
The standalone-clone promise holds, and the specific thing that would rot, a remediation that names the install command but not the `PATH` export, now fails a check rather than waiting for a confused user to report it.
