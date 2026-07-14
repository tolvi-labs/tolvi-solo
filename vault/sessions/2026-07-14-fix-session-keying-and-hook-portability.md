---
tags: [session, tolvi-solo]
date: 2026-07-14
status: active
---

## Session, harden vault routing for git worktrees

### What happened
- Root-caused a vault-routing bug hit while running tolvi-solo across a fleet of parallel Claude Code agents in git worktrees: `find_vault()` in both hooks walks the filesystem upward to the first `vault/.vault-meta.json`, so a worktree nested inside the main repo (or one whose checkout carries no `vault/` of its own) has the walk climb past it and bind to the parent repo's vault — silently misrouting session notes before any commit or PR.
- Fixed `find_vault()` in both hooks to prefer `git rev-parse --show-toplevel`'s own vault first, falling back to the existing filesystem walk (preserves behavior for non-git dirs and vaults nested below the git root).
- Added an ancestor-fallback guard in `tolvi-sync`: when resolution falls back to an ancestor vault, warn by default (`decision:allow` + `additionalContext` surfacing the misroute) rather than silently leaking; `TOLVI_STRICT_WORKTREE=1` hard-blocks instead. Warn-by-default was chosen over block-by-default to avoid false positives for legitimate layouts (vault nested below git root, deliberately shared single-vault setups).
- Confirmed session-keying already derives from the same resolved root as vault-resolution (`session_slug()` reads the branch after `cd "$REPO_ROOT"`), so the `find_vault()` fix corrects both at once — no separate keying alignment was needed.
- Documented the worktree convention in `README.md` (siblings not nested, each worktree owns its own tracked `vault/`, sanity-check via `git rev-parse --show-toplevel`) and added a two-line pointer from `install.sh`'s post-install output. Fixed a stale README line that described the commit gate as keyed "for today" rather than by branch/issue.
- Verified end-to-end against scratch repos with real `git worktree add` checkouts: nested worktree with its own vault resolves to itself; nested worktree without a vault warns (and blocks under strict mode); ordinary single-repo behavior is unchanged; non-git directories still resolve via the fallback walk; `tolvi-recall` still surfaces recent sessions.
- Separately reviewed a related bug report from the fleet-standards plugin's vendored `tolvi-solo-sync` (a different, more elaborate script that keys sessions off GitHub `Closes #N` / branch-embedded issue numbers / milestone tokens, parsed from commit-message text). Confirmed this repo's `session_slug()` never parses commit text — only the branch name — so it isn't exposed to that failure mode, and the fleet-standards script already carries its own fix. Decided to keep this PR scoped to the worktree fix rather than porting that keying redesign in.

### Files touched
- `hooks/tolvi-sync` — `find_vault()` git-anchoring; new ancestor-fallback guard after `REPO_ROOT` resolution.
- `hooks/tolvi-recall` — same `find_vault()` git-anchoring, kept byte-identical to tolvi-sync.
- `README.md` — new "Using tolvi-solo with git worktrees" section; fixed stale commit-gate wording.
- `install.sh` — two-line post-install pointer to the new README section.

### Left open
- None for this PR. Out of scope, noted for later: factoring the now-duplicated `find_vault()` into a shared sourced file; the write-time CWD leak (agent-side, fixed via agent instructions, not a hook concern); any decision to port the fleet-standards plugin's commit-message-based keying scheme into tolvi-solo itself.
