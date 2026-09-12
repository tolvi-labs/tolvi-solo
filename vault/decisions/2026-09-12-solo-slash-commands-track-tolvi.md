---
tags: [decision, tolvi-solo]
date: 2026-09-12
repo: tolvi-solo
status: active
ticket: none
user_impact: high
product_area: Claude Code integration
---

# Solo's slash commands are downstream copies of tolvi's, and divergence is a bug

**Date:** 2026-09-12
**Repo:** tolvi-solo

## Why
`tolvi-solo/commands/` and `tolvi/integrations/claude-code/commands/` carry the same three slash commands. They had drifted: `tolvi`'s `tolvi-recall.md` gained dual-vault routing support, and Solo's copy stayed on the older flat version that only reads the local `vault/sessions/`.

That divergence was not cosmetic, and this repo was already losing to it. `tolvi-solo` is itself a routed checkout, so its session notes live in the private vault rather than in `vault/sessions/`, which stops at an older date. Running `/tolvi-recall` here would have read the local directory, reported a stale session as the most recent, and said nothing about being wrong. It is the same silent-wrong-answer failure the preflight work spent the day removing, arriving through a different door.

The tempting reading was that Solo's simpler copy is deliberate, since routing is an org concern and Solo is the single-builder product. It does not hold: the routing branch is inert when `vault/.vault-routing.local.json` is absent, which is the case for every public user, so carrying it costs them nothing and fixes internal checkouts.

## How
- `commands/tolvi-recall.md` is synced byte-for-byte from `tolvi`'s copy, which is the canonical one.
- The rule going forward is that these files are downstream. A change belongs in `tolvi` first and is copied here, not authored in both places.
- Duplication that cannot be shared, because a standalone clone cannot depend on a sibling, is pinned by `scripts/check-conventions.sh`. See [[2026-09-12-standalone-clone-duplicates-deliberately]].

## Outcome
Recall reports the correct session in a routed Solo checkout, and the reason a divergence here is a defect rather than a local variant is written down.
