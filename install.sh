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

  cp "$HOOKS_SRC/tolvi-recall" "$CLAUDE_DIR/hooks/tolvi-solo-recall"
  cp "$HOOKS_SRC/tolvi-sync"   "$CLAUDE_DIR/hooks/tolvi-solo-sync"
  chmod +x "$CLAUDE_DIR/hooks/tolvi-solo-recall"
  chmod +x "$CLAUDE_DIR/hooks/tolvi-solo-sync"

  local RECALL_HOOK="$CLAUDE_DIR/hooks/tolvi-solo-recall"
  local SYNC_HOOK="$CLAUDE_DIR/hooks/tolvi-solo-sync"

  [[ ! -f "$SETTINGS_FILE" ]] && echo "{}" > "$SETTINGS_FILE"

  # Wire hooks into settings.json via Python (ships with macOS, no extra deps)
  python3 - "$SETTINGS_FILE" "$RECALL_HOOK" "$SYNC_HOOK" <<'PYEOF'
import json, sys

settings_path, recall_hook, sync_hook = sys.argv[1], sys.argv[2], sys.argv[3]

with open(settings_path) as f:
  s = json.load(f)

hooks = s.setdefault("hooks", {})

ss = hooks.setdefault("SessionStart", [])
recall_entry = {"type": "command", "command": recall_hook}
if not any(h.get("command") == recall_hook for h in ss):
  ss.append(recall_entry)

ptu = hooks.setdefault("PreToolUse", [])
sync_entry = {"matcher": "Bash", "hooks": [{"type": "command", "if": "Bash(git commit*)", "command": sync_hook}]}
if not any(any(h.get("command") == sync_hook for h in e.get("hooks", [])) for e in ptu):
  ptu.append(sync_entry)

with open(settings_path, "w") as f:
  json.dump(s, f, indent=2)
  f.write("\n")
PYEOF

  echo "  Claude Code hooks installed (scope: $HOOKS_SCOPE)"
  echo "    SessionStart         → tolvi-solo-recall (vault context before first message)"
  echo "    PreToolUse(git commit) → tolvi-solo-sync (blocks commit until session note exists)"
}

install_commands() {
  local CMD_SRC="$SCRIPT_DIR/commands"
  [[ -d "$CMD_SRC" ]] || return 0

  local CLAUDE_DIR
  if [[ "$HOOKS_SCOPE" == "user" ]]; then
    CLAUDE_DIR="${HOME}/.claude"
  else
    CLAUDE_DIR="$REPO_ROOT/.claude"
  fi
  if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo "  ⚠ $CLAUDE_DIR not found — skipping slash commands"
    return
  fi

  mkdir -p "$CLAUDE_DIR/commands"
  local f n
  for f in "$CMD_SRC"/*.md; do
    n="$(basename "$f")"
    if [[ -e "$CLAUDE_DIR/commands/$n" ]]; then
      echo "    ⚠ /${n%.md} exists — skipping (remove it to reinstall)"
    else
      cp "$f" "$CLAUDE_DIR/commands/$n"
      echo "    installed /${n%.md}"
    fi
  done
  echo "  Slash commands → $CLAUDE_DIR/commands/  (/tolvi-recall, /tolvi-sync, /tolvi-commit)"
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
[[ "$WITH_HOOKS" == "true" ]] && install_commands

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
