---
tags: [decision, tolvi-solo]
date: 2026-09-12
repo: tolvi-solo
status: active
ticket: none
user_impact: medium
product_area: Install / distribution
---

# Stack skills ship from their own product repos, and the installer symlinks them from siblings

**Date:** 2026-09-12
**Repo:** tolvi-solo

## Why
This was misread from the outside during a cross-repo audit, badly enough to be worth writing down. Because `tolvi-bastion`, `tolvi-guild`, and `tolvi-magellan` appear in neither `tolvi` nor `tolvi-solo`, the conclusion drawn was that they ship with nothing and public users never get them. That is wrong. Each skill lives in its own product repo (`bastion/skills/tolvi-bastion` and so on), which is the right home: the skill and the product it documents version together.

What made the misreading easy is that `install_stack_skills` resolves them from sibling checkouts in the workspace parent, so the paths only exist on a machine that has cloned the siblings. Absence in this repo looks like absence everywhere.

The audit did find one real defect underneath the wrong conclusion: `tolvi-magellan` had a `case` branch but no entry in the `for` loop, so the branch was unreachable and the skill silently never installed. Nothing failed and nothing warned, because a skill that is never iterated is never missed.

## How
- The loop now runs `tolvi-guild tolvi-bastion tolvi-magellan vault-health`, in stack order (comprehend, harden, compile) rather than the order they happened to be added.
- `scripts/check-conventions.sh` asserts the loop and the `case` branches agree in both directions: a name in the loop with no branch, and a branch with no loop entry, both fail. The second direction is the exact shape of the magellan bug.
- Missing siblings stay a warning rather than an error, since a user who has cloned only `tolvi-solo` should still get a working vault.

## Outcome
All three stack skills install when their repos are present, the failure mode that hid magellan for an unknown period now fails a check, and the distribution model is written down so the next audit does not have to infer it from an absence.
