---
description: Surface recent sessions and active decisions from the vault before starting work.
---

You are running /tolvi-recall. Surface vault context before doing any work.

<!-- PREFLIGHT:BEGIN -->
## Preflight — say it once if the CLI is missing

Before the steps below, check whether the `tolvi` CLI is available:

    command -v tolvi

**If it is present**, use it. It is one invocation, it discovers the vault itself, and it does not raise a permission prompt per file.

**If it is absent**, fall back to reading the vault directly (the steps below work either way), and tell the user exactly once per conversation:

> `!` tolvi CLI not on PATH. Reading the vault directly, which works but skips
> semantic retrieval and costs one shell call per step. To fix:
> `go install github.com/tolvi-labs/tolvi/cli/cmd/tolvi@latest`, then
> `export PATH="$PATH:$(go env GOPATH)/bin"`. Verify with `tolvi doctor`.

Do not tell the user to run `tolvi doctor` as the fix here. This branch only runs when the binary is unreachable, so `tolvi doctor` is unreachable too; it is the verification step after the install, not the remedy. Point at `tolvi doctor` only when the binary exists and something else is wrong.

**Once per conversation means once.** If you have already reported this in the current conversation, do not repeat it — later commands in the same session stay quiet. You know what you have already said; no marker file is needed. A user who has chosen not to install the CLI should not be told four times in one session, because a warning repeated that often stops being read.

Never silently degrade. The fallback path is legitimate and produces real answers, but the user has to learn once that they are on it, or a broken install looks identical to a working one.
<!-- PREFLIGHT:END -->

If the `tolvi` CLI is available, run `tolvi recall` and present its output. That is one invocation and the preferred path — prefer it whenever the binary exists.

Otherwise read the vault directly, using the commands below **verbatim**. They are loop-free on purpose: a `for f in *.md; do ... done` loop is not prefix-matchable by Claude Code's permission system, so every loop raises a permission prompt on every recall. Each command here is a single invocation covered by an ordinary `Bash(rg:*)` / `Bash(ls:*)` allow rule. Do not "simplify" them back into a loop.

1. **Discover the vault** — walk up to the first `vault/.vault-meta.json`:

       ls vault/.vault-meta.json ../vault/.vault-meta.json ../../vault/.vault-meta.json 2>/dev/null | head -1

   If nothing prints, say so and stop.

2. **Sessions** — date-named files, so the newest sorts last:

       ls -1 vault/sessions/ | tail -3

   Then read the newest file with the Read tool (no shell needed) and surface its latest `## [HH:MM] Session — ...` heading plus any `### Left open` items.

3. **Decisions** — one call covers status and title across every decision:

       rg -N --no-heading -H --sort path '^(status:|# )' vault/decisions/ | tail -40

   Output interleaves `path:status:` with `path:# Title` per file. Skip any whose `status` is `superseded`, `deprecated`, or `draft` (missing = `active`). Surface up to ~10 active, newest first, as `slug — title`.

4. **Patterns** — not loaded at recall; query on demand with `tolvi ask`.

Output:

```
RECALL SUMMARY
──────────────────────────────────────────
Last session:  [date — heading]
Left open:
  [bullet per item, or none]
Decisions:     [N relevant | none]
  [slug — title  (status: X if not active)]
──────────────────────────────────────────
```

Then ask what to focus on.
