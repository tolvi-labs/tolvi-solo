#!/usr/bin/env bash
# Repo conventions check. Two assertions that would otherwise rot silently:
#
#  1. install.sh must never suggest `go install` without also naming the PATH
#     export. `go install` writes to $(go env GOPATH)/bin, which is frequently
#     not on PATH, so an install that mentions only the install command looks
#     successful while leaving every slash command on the silent fallback path.
#
#  2. Every slash command's PREFLIGHT block must match commands/_preflight.md.
#     Hand-maintained copies drift; this pins them.
#
# tolvi-solo is a standalone clone and cannot depend on the tolvi repo, so both
# the remediation text and this check are deliberate duplicates of tolvi's.
# See tolvi/.github/scripts/ for the sibling copies.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

fail=0

# ── 1. install.sh remediation ────────────────────────────────────────────
if grep -q 'go install github.com/tolvi-labs/tolvi' install.sh; then
  if ! grep -q 'go env GOPATH' install.sh; then
    echo "✗ install.sh: mentions 'go install' but never 'go env GOPATH'."
    echo "    A user who follows it ends up with an unreachable binary."
    fail=1
  elif ! grep -qE 'export PATH|PATH=' install.sh; then
    echo "✗ install.sh: mentions 'go install' but never a PATH export."
    fail=1
  else
    echo "✓ install.sh: go install remediation names the PATH export"
  fi
fi

# ── 2. preflight block in sync ───────────────────────────────────────────
src="commands/_preflight.md"
extract() { sed -n '/<!-- PREFLIGHT:BEGIN -->/,/<!-- PREFLIGHT:END -->/p' "$1"; }
if [ -f "$src" ]; then
  canonical="$(extract "$src")"
  for f in commands/*.md; do
    [ "$(basename "$f")" = "_preflight.md" ] && continue
    got="$(extract "$f")"
    if [ -z "$got" ]; then
      echo "⚠ $f: no PREFLIGHT block (add one if it uses the CLI)"
      continue
    fi
    if [ "$got" != "$canonical" ]; then
      echo "✗ $f: PREFLIGHT block has drifted from $src"
      fail=1
    else
      echo "✓ $f: preflight in sync"
    fi
  done
else
  echo "✗ missing $src"
  fail=1
fi

# ── 3. every stack skill the installer wires is a real source ────────────
# The installer pulls tolvi-guild, tolvi-bastion, and tolvi-magellan from
# sibling product repos. A skill named in the loop but absent from the case
# statement (or vice versa) installs nothing and says nothing, which is how
# tolvi-magellan went missing.
loop_names="$(sed -n 's/^  for name in \(.*\); do$/\1/p' install.sh | head -1)"
if [ -n "$loop_names" ]; then
  for n in $loop_names; do
    if ! grep -qE "^      $n\)" install.sh; then
      echo "✗ install.sh: '$n' is in the stack-skill loop but has no case branch."
      fail=1
    fi
  done
  for n in $(grep -oE '^      tolvi-[a-z]+\)' install.sh | tr -d ')' | tr -d ' '); do
    case " $loop_names " in
      *" $n "*) ;;
      *) echo "✗ install.sh: '$n' has a case branch but is not in the loop, so it never installs."; fail=1 ;;
    esac
  done
  echo "✓ install.sh: stack-skill loop and case branches agree ($loop_names)"
fi

[ "$fail" -eq 0 ] || { echo ""; echo "See scripts/check-conventions.sh for why each rule exists."; exit 1; }
echo ""
echo "All conventions checks passed."
