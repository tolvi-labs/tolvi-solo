---
tags: [decision, tolvi-solo]
date: 2026-10-05
repo: tolvi-solo
status: active
ticket: none
user_impact: high
product_area: Claude Code integration
---

# The commit gate checks its own command, and a project-scope install carries no machine paths

**Date:** 2026-10-05
**Repo:** tolvi-solo

## Why
A user who installed tolvi-solo into a shared repo hit three bugs at once: the commit gate blocked every shell command instead of only commits, the session-start recall hook never ran, and the hook and skill paths pointed at the installer's own machine, so the install was broken for every teammate who cloned the repo.

## How
- `hooks/tolvi-sync` reads the PreToolUse payload from stdin and exits silently unless `tool_input.command` is a `git commit` (also matching `git -C <dir> commit`, `-c` options, and a commit after `&&`, `;`, `|` or `(`). The settings entry keeps its `"if": "Bash(git commit*)"` filter, but the reporter saw Claude Code ignore it and block a `python3` command, so the gate no longer depends on it. Before this, every Bash call staged `vault/` and could be blocked.
- The SessionStart entry is written as `{"hooks": [{"type": "command", ...}]}`. The old installer appended the bare `{"type": "command", ...}` object, which Claude Code does not run, so recall never fired on any install.
- Re-running the installer repairs an old install: it strips every entry whose command names `tolvi-solo-recall` or `tolvi-solo-sync` (bare or wrapped, absolute path or not), drops any wrapper left empty, and appends the current entries. Other hooks in the same arrays are preserved, and repeated runs do not duplicate entries.
- Project scope writes `"$CLAUDE_PROJECT_DIR"/.claude/hooks/tolvi-solo-*` as the hook command, because `.claude/settings.json` is committed and runs on other checkouts. User scope keeps absolute `~/.claude/hooks/...` paths, which are correct there because nothing is shared.
- Project scope copies the stack skills (`vault-health`, and `tolvi-guild`, `tolvi-bastion`, `tolvi-magellan` when their sibling clones exist) into `.claude/skills/`. User scope still symlinks them, so a `git pull` in the clone updates the skill. The report named only vault-health, but the sibling skills had the same dangling-symlink failure and were fixed with it.
- Not changed: the gate's pass path still emits a top-level `"decision": "allow"`, which is not a documented PreToolUse value (the current form is `hookSpecificOutput.permissionDecision`). Left for a separate change.

## Outcome
A project-scope install now works on any teammate's checkout, recall runs at session start, and the commit gate only fires on `git commit`, verified by installing into scratch repos seeded with the old malformed settings and feeding each hook sample payloads.
