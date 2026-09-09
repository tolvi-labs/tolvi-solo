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

# Allowlist the read-only tolvi subcommands so /tolvi-recall and `tolvi ask`
# stop raising a permission prompt on every use. Writes are deliberately NOT
# allowlisted: `tolvi sync` and `tolvi commit` mutate the vault and the git
# history, so they should stay a conscious per-call approval.
allow = s.setdefault("permissions", {}).setdefault("allow", [])
added = [r for r in ("Bash(tolvi recall:*)", "Bash(tolvi ask:*)") if r not in allow]
allow.extend(added)

with open(settings_path, "w") as f:
  json.dump(s, f, indent=2)
  f.write("\n")

if added:
  print("  allowlisted " + ", ".join(added) + " (read-only; sync/commit still prompt)")
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

# Symlinks the Tolvi stack skills so they ship with the suite. tolvi-bastion and
# tolvi-guild come from repos cloned alongside this one; vault-health ships in
# this repo, so it installs whether or not the siblings are present.
install_stack_skills() {
  local parent CLAUDE_DIR
  parent="$(dirname "$SCRIPT_DIR")"   # the tolvi-labs/ workspace
  if [[ "$HOOKS_SCOPE" == "user" ]]; then
    CLAUDE_DIR="${HOME}/.claude"
  else
    CLAUDE_DIR="$REPO_ROOT/.claude"
  fi
  if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo "  ⚠ $CLAUDE_DIR not found — skipping stack skills"
    return
  fi

  mkdir -p "$CLAUDE_DIR/skills"
  local name src dest
  for name in tolvi-bastion tolvi-guild vault-health; do
    case "$name" in
      tolvi-bastion) src="$parent/bastion/skills/tolvi-bastion" ;;
      tolvi-guild)   src="$parent/guild/skills/tolvi-guild" ;;
      vault-health)  src="$SCRIPT_DIR/skills/vault-health" ;;
    esac
    dest="$CLAUDE_DIR/skills/$name"
    if [[ ! -d "$src" ]]; then
      if [[ "$name" == vault-health ]]; then
        echo "    ⚠ $name: source not found at $src (skipping)"
      else
        echo "    ⚠ $name: source not found at $src — clone tolvi-labs/${name#tolvi-} alongside tolvi-solo (skipping)"
      fi
      continue
    fi
    if [[ -e "$dest" || -L "$dest" ]]; then
      echo "    ⚠ /$name exists — skipping (remove it to reinstall)"
      continue
    fi
    ln -s "$src" "$dest"
    echo "    installed /$name (symlink → $src)"
  done
  echo "  Stack skills → $CLAUDE_DIR/skills/  (/tolvi-bastion, /tolvi-guild, /vault-health)"
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
[[ "$WITH_HOOKS" == "true" ]] && install_stack_skills

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
