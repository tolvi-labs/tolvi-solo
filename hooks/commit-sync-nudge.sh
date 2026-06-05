#!/usr/bin/env bash
# PostToolUse(git commit) hook — nudge to log the session after a commit.
# Fires once per commit; never mid-task. Silent when no vault is found.
set -euo pipefail

# Find vault by walking up from cwd
find_vault() {
  local dir="${1:-$PWD}"
  while [[ "$dir" != "/" ]]; do
    [[ -f "$dir/vault/.vault-meta.json" ]] && echo "$dir/vault" && return
    dir="$(dirname "$dir")"
  done
  return 1
}

find_vault "$PWD" &>/dev/null || exit 0

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Vault is active in this repo. When this task wraps up, offer to log a session note to vault/sessions/ — one line on what changed and what is left open. Do not interrupt current work."}}'
