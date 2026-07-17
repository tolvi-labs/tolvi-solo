---
tags: [session, tolvi-solo]
date: 2026-07-16
status: active
---

## Session, split the bundled PR — session-file collision fix

### What happened
- Trimmed PR #1 down to this one fix (it originally bundled four unrelated fixes); the other three now ship as their own PRs (#2, #3, #4), each independently reviewable and mergeable in any order.
- `tolvi-sync` keyed every session note purely by date: `vault/sessions/$TODAY.md`. On a repo with more than one contributor or agent working the same day, everyone's commits landed in the same file — not a logical conflict, just noisy diff churn on shared vault prose that turned into real PR merge conflicts.
- The obvious fix — key by branch instead — fails the opposite way: on the default branch, every session becomes `<date>-main`, which collapses right back into one shared file and is useless as a discriminator.
- The fix keys the session file by, in order: (1) an issue id or slug parsed from the branch name when one exists — Jira/Linear-style `ABC-123`, a leading `#42`/`42-`, or the slugified branch itself; (2) the Claude session id (first 8 chars) when there's no usable branch (default branch or detached HEAD) — this is what stops two agents on the same default branch on the same day from colliding; (3) plain date, if neither is available.
- Added a blocklist (`fix`, `feat`, `chore`, `wip`, etc.) so branches like `alice/fix-2` don't get mistaken for a project-key issue id and collide with `bob/fix-2` on session file `fix-2` — both now fall through to full-branch slugification instead.
- Hook now skips reading stdin when it's a TTY, so running the script by hand for testing doesn't hang waiting for a payload that will never arrive.
- `commands/tolvi-commit.md` updated: if the hook blocks naming a different session file than the one already written (happens on the default branch, since only the hook sees the Claude session id), `mv` the note to the hook-named path and retry instead of writing a duplicate.
- Verified: branch/session-id keying on `main`, `feature/PROJ-123-add-auth`, `spike-thing`; the block→allow transition once the named file exists with a `## ` heading; the `alice/fix-2` vs `bob/fix-2` collision regression; stdin/TTY behavior.

### Files touched
- `hooks/tolvi-sync` — `session_slug()`, branch/issue/session-id keying, TTY-stdin skip.
- `commands/tolvi-commit.md`, `commands/tolvi-sync.md` — document the new keying scheme and the mv-and-retry instruction.

### Left open
- None for this PR. Out of scope, shipping separately: the empty-vault crash fix (#2), installer portability fix (#3), and the git-worktree vault-routing fix (#4) — none of the four depend on each other.
