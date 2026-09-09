---
name: vault-health
description: Deterministic health check for a tolvi-format vault. Reports empty tags, unrecognized status values, duplicate titles, unfilled template placeholders, escaped unicode, and unparseable frontmatter, graded by dimension. Use when spot-checking any vault provisioned by tolvi-solo or managed by the tolvi CLI.
---

# Vault Health

Runs `scripts/vault_health.py` against a `vault/` directory and reports defects that degrade retrieval — the things that make a note fail to surface, surface twice, or surface as noise.

**Announce at start:** "Using vault-health to check <path> for retrieval-degrading defects."

## Usage

```
/vault-health <path-to-vault-dir>
```

`<path-to-vault-dir>` is the `vault/` directory itself, not the repo root that contains it.

## Running it

The script sits beside this file at `scripts/vault_health.py`. Resolve it against **this skill's own directory** — the base directory given when the skill loads — not against the current repo. The skill is normally installed as a symlink in `~/.claude/skills/vault-health` and invoked from whatever repo you happen to be in, so a path relative to the working directory will not find it.

```bash
uv run --with pyyaml python <skill-dir>/scripts/vault_health.py <path-to-vault-dir>
```

`uv` fetches PyYAML on the fly, so there is no install step. On a plain interpreter, `pip install -r <skill-dir>/scripts/requirements.txt` first — it pins the one runtime dependency.

To verify the checks themselves, which is only useful when working on the skill:

```bash
cd <skill-dir>/scripts && uv run --with pyyaml --with pytest python -m pytest tests/
```

Print the full console output back to the user — do not summarize or truncate it further; the script already truncates long finding lists itself.

## Checks

| check_id | Severity | Catches |
|---|---|---|
| `empty-tags` | high | `tags:` missing or empty — the note will not surface by tag |
| `duplicate-title` | high | Two notes whose `# Heading` slugifies identically |
| `template-placeholder` | high | A note copied from a template and left partly unfilled |
| `status-enum` | medium | A `status:` value outside the tolvi-format vocabulary |
| `unicode-escaping` | low | Literal `\uXXXX` sequences that should be real characters |
| `unparseable-frontmatter` | — | Reported separately at the top; excluded from all grades |

Grades run over five dimensions — tags, lifecycle, dedup, completeness, unicode. Each scores as the percentage of evaluable notes that no finding in that dimension touched. **The overall grade is the unweighted mean of the five, so one dimension at F can hide behind a decent headline letter — read the per-dimension line.**

## Scope

- Checks only what tolvi-format-v1 defines: frontmatter `tags` and `status`, the `# Heading` a note opens with, and unfilled template markers. `related:` and wikilinks are never checked.
- Files under `templates/` are skipped. They are unfilled by design, and every placeholder check would fire on them.
- The title is the note's first `# Heading`, not a frontmatter field — tolvi-format has no `title:` key.
- `template-placeholder` looks in frontmatter values and in headings, never in body prose. A note that documents the `sessions/YYYY-MM-DD.md` naming convention is prose, not a half-filled template.
- An absent `status:` is treated as `active` by convention, not as a defect.
- Deterministic only — no LLM calls. Fuzzy or near-duplicate title matching is out of scope; only exact slug collisions are caught.
- One vault directory per run.
