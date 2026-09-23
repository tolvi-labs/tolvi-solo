#!/usr/bin/env bash
# pack-manifest-check.sh — fails (exit 1) when a pack's manifest, its templates
# on disk, and the README table disagree.
#
# packs/<name>/pack.json is the machine-readable source of truth for a pack.
# Before it existed, a pack's names, statuses and descriptions lived only in
# prose tables and the installer discovered packs with a bare `ls`, so nothing
# could read a pack without parsing Markdown. The tolvi CLI vendors these
# manifests, which makes drift here a problem in two repos rather than one.
#
# Checked, in both directions:
#   - every packs/<dir> has a pack.json whose name matches the directory
#   - every template listed in pack.json exists, and every template on disk is
#     listed, with a non-empty "use"
#   - the root README's Packs table agrees with each manifest's status
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

fail=0

for dir in packs/*/; do
  name="$(basename "$dir")"
  manifest="$dir/pack.json"

  if [ ! -f "$manifest" ]; then
    echo "✗ $name: no pack.json"
    fail=1
    continue
  fi

  declared_name="$(node -p "require('./$manifest').name")"
  if [ "$declared_name" != "$name" ]; then
    echo "✗ $name: pack.json declares name \"$declared_name\""
    fail=1
  fi

  # Templates, both directions.
  listed="$(node -p "require('./$manifest').templates.map(t => t.file).sort().join('\n')")"
  ondisk="$(find "$dir/templates" -name '*.md' -type f -exec basename {} \; | sort)"
  if [ "$listed" != "$ondisk" ]; then
    echo "✗ $name: pack.json templates and templates/ disagree"
    diff <(echo "$listed") <(echo "$ondisk") | head -10 || true
    fail=1
  fi

  # A template with no "use when" is a row nobody can render.
  if ! node -e "
    const m = require('./$manifest');
    const bad = m.templates.filter(t => !t.use || !t.use.trim()).map(t => t.file);
    if (bad.length) { console.log('✗ $name: no \"use\" for ' + bad.join(', ')); process.exit(1); }
  "; then
    fail=1
  fi

  # The README table is what a person reads; the manifest is what a tool reads.
  status="$(node -p "require('./$manifest').status")"
  row="$(grep -E "^\| \`$name\` \|" README.md || true)"
  if [ -z "$row" ]; then
    echo "✗ $name: no row in the README Packs table"
    fail=1
  elif [ "$status" = "available" ] && ! echo "$row" | grep -q '✅'; then
    echo "✗ $name: pack.json says available, the README table does not"
    fail=1
  elif [ "$status" = "planned" ] && ! echo "$row" | grep -qi 'planned'; then
    echo "✗ $name: pack.json says planned, the README table does not"
    fail=1
  fi
done

# A README row claiming a shipped pack that has no directory is the other
# direction of the same lie.
# shellcheck disable=SC2016  # the backticks below are literal Markdown
while read -r name; do
  [ -d "packs/$name" ] || { echo "✗ README lists \`$name\` as shipped, but packs/$name does not exist"; fail=1; }
done < <(grep -oE "^\| \`[a-z]+\` \| ✅" README.md | grep -oE '`[a-z]+`' | tr -d '`')

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "packs/<name>/pack.json is the source of truth. See .github/scripts/pack-manifest-check.sh."
  exit 1
fi

echo "✓ $(find packs -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') pack manifests agree with their templates and the README"
