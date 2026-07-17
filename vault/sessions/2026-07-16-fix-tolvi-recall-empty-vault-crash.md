---
tags: [session, tolvi-solo]
date: 2026-07-16
status: active
---

## Session, split the bundled PR — empty-vault crash fix

### What happened
- Split this fix out of the originally-bundled PR #1 (which mixed four unrelated fixes into one diff) into its own standalone PR, per the maintainer-facing preference for smaller, independently reviewable chunks.
- Fixed `hooks/tolvi-recall` crashing on a fresh install: the script runs under `set -euo pipefail`, and right after install `vault/decisions` and `vault/sessions` are empty, so `ls "$DIR"/*.md` fails to glob-expand and exits non-zero, aborting the SessionStart hook. `grep -v '.gitkeep'` compounded it by also exiting non-zero on no matches.
- Swapped `ls "$DIR"/*.md | ...` for `find "$DIR" -maxdepth 1 -name '*.md' | ...` (exits 0 on no matches) and added `|| true` on the assignments as a second line of defense. Dropped the now-redundant `grep -v '.gitkeep'`.
- Verified against all three vault states (both dirs empty, one populated, both populated) — all exit 0 with correct output when content exists.

### Files touched
- `hooks/tolvi-recall` — `ls` → `find` + `|| true` on the recent-sessions and active-decisions assignments.

### Left open
- None. This is the complete, isolated diff for this fix — extracted cleanly from the bundled PR with no overlap with the other three fixes (session-keying, installer portability, worktree routing), each shipping as its own PR.
