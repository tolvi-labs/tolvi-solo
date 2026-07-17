---
tags: [session, tolvi-solo]
date: 2026-07-16
status: active
---

## Session, split the bundled PR — installer portability fix

### What happened
- Split this fix out of the originally-bundled PR #1 into its own standalone PR, per the maintainer-facing preference for smaller, independently reviewable chunks.
- Fixed `install.sh`: with `--hooks-scope project`, the installer wrote an absolute path — `$REPO_ROOT/.claude/hooks/tolvi-solo-recall` — into the `command` field of a `.claude/settings.json` meant to be committed. That only works on the machine that ran the installer; anyone else cloning the repo gets a hook pointing at a path that doesn't exist on their machine.
- Fixed by splitting the path used for `cp`/`chmod` (still an absolute, real path — needed to actually write the file) from the path written into the JSON `command` field. For `--hooks-scope project`, the JSON now gets the literal string `${CLAUDE_PROJECT_DIR}/.claude/hooks/tolvi-solo-recall` — Claude Code's documented placeholder for exactly this, expanded per-clone at hook-invocation time. `--hooks-scope user` is unchanged: the absolute `$HOME` path is correct there since that config is per-machine and never committed.
- Verified: `--hooks-scope project` produces a `settings.json` with the literal `${CLAUDE_PROJECT_DIR}/...` command string; `--hooks-scope user` still uses the absolute `$HOME` path; re-running either doesn't duplicate hook entries.

### Files touched
- `install.sh` — split `RECALL_HOOK`/`SYNC_HOOK` path resolution by hooks-scope.

### Left open
- None. This is the complete, isolated diff for this fix — extracted cleanly from the bundled PR with no overlap with the other three fixes (session-keying, empty-vault crash, worktree routing), each shipping as its own PR.
