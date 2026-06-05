#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PACK="engineer"
WITH_HOOKS=false
HOOKS_SCOPE="user"

usage() {
  echo "Usage: $0 [--pack <name>] [--with-hooks] [--hooks-scope user|project]"
  echo ""
  echo "  --pack           Schema pack to install (default: engineer)"
  echo "  --with-hooks     Wire Claude Code session hooks"
  echo "  --hooks-scope    user (all repos, default) or project (this repo only)"
  exit 1
}

install_hooks() {
  local HOOKS_SRC="$SCRIPT_DIR/hooks"

  if [[ "$HOOKS_SCOPE" == "user" ]]; then
    local CLAUDE_DIR="${HOME}/.claude"
  else
    local CLAUDE_DIR="$REPO_ROOT/.claude"
  fi
  local SETTINGS_FILE="$CLAUDE_DIR/settings.json"

  if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo "  ⚠ Claude Code config dir not found at $CLAUDE_DIR — skipping hooks"
    echo "    Install Claude Code first, then re-run with --with-hooks"
    return
  fi

  mkdir -p "$CLAUDE_DIR/hooks"

  cp "$HOOKS_SRC/session-recall.sh" "$CLAUDE_DIR/hooks/tolvi-solo-session-recall.sh"
  cp "$HOOKS_SRC/commit-sync-nudge.sh" "$CLAUDE_DIR/hooks/tolvi-solo-commit-sync-nudge.sh"
  chmod +x "$CLAUDE_DIR/hooks/tolvi-solo-session-recall.sh"
  chmod +x "$CLAUDE_DIR/hooks/tolvi-solo-commit-sync-nudge.sh"

  local RECALL_HOOK="$CLAUDE_DIR/hooks/tolvi-solo-session-recall.sh"
  local NUDGE_HOOK="$CLAUDE_DIR/hooks/tolvi-solo-commit-sync-nudge.sh"

  [[ ! -f "$SETTINGS_FILE" ]] && echo "{}" > "$SETTINGS_FILE"

  # Wire hooks into settings.json via Python (ships with macOS, no extra deps)
  python3 - "$SETTINGS_FILE" "$RECALL_HOOK" "$NUDGE_HOOK" <<'PYEOF'
import json, sys

settings_path, recall_hook, nudge_hook = sys.argv[1], sys.argv[2], sys.argv[3]

with open(settings_path) as f:
  s = json.load(f)

hooks = s.setdefault("hooks", {})

ss = hooks.setdefault("SessionStart", [])
recall_entry = {"type": "command", "command": recall_hook}
if not any(h.get("command") == recall_hook for h in ss):
  ss.append(recall_entry)

ptu = hooks.setdefault("PostToolUse", [])
nudge_entry = {"matcher": "Bash(git commit*)", "hooks": [{"type": "command", "command": nudge_hook}]}
if not any(h.get("matcher") == nudge_entry["matcher"] for h in ptu):
  ptu.append(nudge_entry)

with open(settings_path, "w") as f:
  json.dump(s, f, indent=2)
  f.write("\n")
PYEOF

  echo "  Claude Code hooks installed (scope: $HOOKS_SCOPE)"
  echo "    SessionStart            → tolvi-solo-session-recall"
  echo "    PostToolUse(git commit) → tolvi-solo-commit-sync-nudge"
}

# --- parse flags ---

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pack) PACK="$2"; shift 2 ;;
    --with-hooks) WITH_HOOKS=true; shift ;;
    --hooks-scope) HOOKS_SCOPE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown flag: $1"; usage ;;
  esac
done

PACK_DIR="$SCRIPT_DIR/packs/$PACK"
if [[ ! -d "$PACK_DIR" ]]; then
  echo "Pack '$PACK' not found. Available packs:"
  ls "$SCRIPT_DIR/packs/"
  exit 1
fi

if [[ "$HOOKS_SCOPE" != "user" && "$HOOKS_SCOPE" != "project" ]]; then
  echo "--hooks-scope must be 'user' or 'project'"
  exit 1
fi

# --- provision vault ---

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKSPACE="$(basename "$REPO_ROOT")"
VAULT_DIR="$REPO_ROOT/vault"

echo "→ Provisioning vault at $VAULT_DIR"
echo "  pack:      $PACK"
echo "  workspace: $WORKSPACE"

mkdir -p "$VAULT_DIR/decisions" "$VAULT_DIR/patterns" "$VAULT_DIR/sessions" "$VAULT_DIR/templates"

cat > "$VAULT_DIR/.vault-meta.json" <<EOF
{
  "workspace": "$WORKSPACE",
  "pack": "$PACK",
  "format": "tolvi-format-v1",
  "created": "$(date +%Y-%m-%d)"
}
EOF

cp "$PACK_DIR/templates/"* "$VAULT_DIR/templates/"

echo "  vault structure created"
echo "  templates copied from pack: $PACK"

[[ "$WITH_HOOKS" == "true" ]] && install_hooks

echo ""
echo "✓ Vault ready at $VAULT_DIR"
echo ""
echo "Next steps:"
echo "  1. Write your first decision:"
echo "     cp $VAULT_DIR/templates/decision.md $VAULT_DIR/decisions/$(date +%Y-%m-%d)-first-decision.md"
echo ""
if command -v tolvi &>/dev/null; then
  echo "  2. Query your vault:  tolvi ask \"what decisions have I made?\""
else
  echo "  2. Install tolvi CLI for natural-language vault queries:"
  echo "     go install github.com/tolvi-labs/tolvi/cli/cmd/tolvi@latest"
fi
