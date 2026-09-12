"""Deterministic health checks for a tolvi-format vault.

Checks only what the tolvi-format-v1 schema actually defines — frontmatter
`tags` and `status`, the `# Heading` a note opens with, and unfilled template
placeholders. `related:` and wikilinks are deliberately never checked.

Files under `templates/` are skipped: they are unfilled by design.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


@dataclass
class Note:
    path: Path
    rel_path: str
    frontmatter: dict | None
    body: str
    raw_text: str
    parse_error: str | None = None
    frontmatter_raw: str = ""


@dataclass
class Finding:
    check_id: str
    severity: str  # "high" | "medium" | "low"
    file: str
    reason: str


# The tolvi-format-v1 status vocabulary. `active` is the implied default when
# the key is absent; the recall skills treat superseded/deprecated/draft as
# filtered-out and everything else as live.
KNOWN_STATUSES = frozenset({"active", "in-progress", "draft", "superseded", "deprecated"})

# Matched as a path segment, not a prefix: the vault may be addressed as
# `vault/` or from a level above it, and `vault/templates/x.md` must skip too.
SKIP_DIRS = frozenset({"templates"})


def is_skipped(rel_path: str) -> bool:
    return bool(SKIP_DIRS & set(Path(rel_path).parts))


def load_notes(vault_dir: Path) -> list[Note]:
    notes = []
    for path in sorted(vault_dir.rglob("*.md")):
        rel_path = str(path.relative_to(vault_dir))
        if is_skipped(rel_path):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - any read failure is a finding, not a crash
            notes.append(Note(path, rel_path, None, "", "", str(exc)))
            continue
        match = FRONTMATTER_RE.match(raw)
        if not match:
            notes.append(Note(path, rel_path, None, raw, raw, "no frontmatter block found"))
            continue
        yaml_block, body = match.group(1), match.group(2)
        try:
            frontmatter = yaml.safe_load(yaml_block)
            if not isinstance(frontmatter, dict):
                raise ValueError("frontmatter is not a mapping")
        except Exception as exc:  # noqa: BLE001 - any parse failure is a finding, not a crash
            notes.append(Note(path, rel_path, None, body, raw, str(exc)))
            continue
        notes.append(Note(path, rel_path, frontmatter, body, raw, frontmatter_raw=yaml_block))
    return notes


_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def extract_heading(body: str) -> str:
    """The note's title is its first `# Heading`, not a frontmatter field."""
    match = _HEADING_RE.search(body)
    return match.group(1) if match else ""


def check_empty_tags(notes: list[Note]) -> list[Finding]:
    findings = []
    for note in notes:
        if note.frontmatter is None:
            continue
        if not note.frontmatter.get("tags"):
            findings.append(Finding("empty-tags", "high", note.rel_path, "tags field is empty or missing"))
    return findings


def check_status_enum(notes: list[Note]) -> list[Finding]:
    findings = []
    for note in notes:
        if note.frontmatter is None:
            continue
        if "status" not in note.frontmatter:
            continue  # absent status means `active` by convention, not a defect
        status = note.frontmatter.get("status")
        if status not in KNOWN_STATUSES:
            findings.append(Finding(
                "status-enum", "medium", note.rel_path,
                f"unrecognized status value: {status!r}",
            ))
    return findings


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    return _SLUG_RE.sub("-", title.strip().lower()).strip("-")


def check_duplicate_titles(notes: list[Note]) -> list[Finding]:
    clusters: dict[str, list[Note]] = {}
    for note in notes:
        if note.frontmatter is None:
            continue
        heading = extract_heading(note.body)
        if not heading:
            continue
        clusters.setdefault(_slugify(heading), []).append(note)

    findings = []
    for slug, members in clusters.items():
        if len(members) < 2:
            continue
        other_files = [m.rel_path for m in members]
        for note in members:
            others = ", ".join(f for f in other_files if f != note.rel_path)
            findings.append(Finding(
                "duplicate-title", "high", note.rel_path,
                f"title slug '{slug}' also used by: {others}",
            ))
    return findings


# Unfilled template markers, scoped to where an unfilled template actually
# shows them. Body prose is deliberately excluded: a note may legitimately
# document the `sessions/YYYY-MM-DD.md` naming convention without being a
# half-filled template. The angle-bracket form requires an internal hyphen so
# it cannot match HTML tags like <br> or <div>.
_FRONTMATTER_PLACEHOLDER_RES = (
    ("date", re.compile(r"YYYY-MM-DD")),
    ("slug", re.compile(r"<[a-z]+(?:-[a-z]+)+>")),
)
_HEADING_PLACEHOLDER_RE = re.compile(r"^#{1,6}\s.*\[HH:MM\]", re.MULTILINE)


def check_template_placeholder(notes: list[Note]) -> list[Finding]:
    findings = []
    for note in notes:
        if note.frontmatter is None:
            continue
        hits = []
        for label, pattern in _FRONTMATTER_PLACEHOLDER_RES:
            found = pattern.findall(note.frontmatter_raw)
            if found:
                hits.append(f"{label} ({found[0]})")
        if _HEADING_PLACEHOLDER_RE.search(note.body):
            hits.append("time ([HH:MM])")
        if hits:
            findings.append(Finding(
                "template-placeholder", "high", note.rel_path,
                f"unfilled template placeholder: {', '.join(hits)}",
            ))
    return findings


_UNICODE_ESCAPE_RE = re.compile(r"\\u[0-9a-fA-F]{4}")


def check_unicode_escaping(notes: list[Note]) -> list[Finding]:
    findings = []
    for note in notes:
        if note.frontmatter is None:
            continue
        matches = _UNICODE_ESCAPE_RE.findall(note.raw_text)
        if matches:
            findings.append(Finding(
                "unicode-escaping", "low", note.rel_path,
                f"{len(matches)} escaped unicode sequence(s) found (e.g. {matches[0]})",
            ))
    return findings


def check_unparseable(notes: list[Note]) -> list[Finding]:
    return [
        Finding("unparseable-frontmatter", "high", n.rel_path, n.parse_error)
        for n in notes if n.parse_error is not None
    ]


def run_all_checks(notes: list[Note]) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_empty_tags(notes))
    findings.extend(check_status_enum(notes))
    findings.extend(check_duplicate_titles(notes))
    findings.extend(check_template_placeholder(notes))
    findings.extend(check_unicode_escaping(notes))
    findings.extend(check_unparseable(notes))
    return findings


DIMENSIONS = {
    "tags": {"empty-tags"},
    "lifecycle": {"status-enum"},
    "dedup": {"duplicate-title"},
    "completeness": {"template-placeholder"},
    "unicode": {"unicode-escaping"},
}

_GRADE_THRESHOLDS = [
    (97, "A+"), (93, "A"), (90, "A-"), (87, "B+"), (83, "B"), (80, "B-"),
    (77, "C+"), (73, "C"), (70, "C-"), (60, "D"),
]

MAX_SHOWN_PER_CHECK = 10
SEVERITY_ORDER = ("high", "medium", "low")


def _grade_letter(pct: float) -> str:
    for min_pct, letter in _GRADE_THRESHOLDS:
        if pct >= min_pct:
            return letter
    return "F"


def _evaluable_count(notes: list[Note]) -> int:
    return len([n for n in notes if n.parse_error is None])


def compute_grades(notes: list[Note], findings: list[Finding]):
    total = _evaluable_count(notes)
    grades = {}
    for dim, check_ids in DIMENSIONS.items():
        affected = {f.file for f in findings if f.check_id in check_ids}
        pct = 100.0 if total == 0 else 100.0 * (total - len(affected)) / total
        grades[dim] = (pct, _grade_letter(pct))
    overall_pct = sum(pct for pct, _ in grades.values()) / len(grades) if grades else 100.0
    return grades, (overall_pct, _grade_letter(overall_pct))


def render_report(vault_dir: Path, notes: list[Note], findings: list[Finding]) -> str:
    lines = [f"VAULT HEALTH — {vault_dir}", "─" * 40, f"Files scanned: {len(notes)}"]

    unparseable = [f for f in findings if f.check_id == "unparseable-frontmatter"]
    if unparseable:
        lines.append(f"Unparseable frontmatter: {len(unparseable)}")

    grades, (_, overall_letter) = compute_grades(notes, findings)
    lines.append(f"Overall grade: {overall_letter}")
    lines.append("")

    grouped_findings = [f for f in findings if f.check_id != "unparseable-frontmatter"]

    by_check: dict[str, list[Finding]] = {}
    for f in grouped_findings:
        by_check.setdefault(f.check_id, []).append(f)

    for severity in SEVERITY_ORDER:
        check_ids = sorted({f.check_id for f in grouped_findings if f.severity == severity})
        if not check_ids:
            continue
        lines.append(severity.upper())
        evaluable = _evaluable_count(notes)
        for check_id in check_ids:
            entries = by_check[check_id]
            pct = 100.0 * len(entries) / evaluable if evaluable else 0.0
            lines.append(f"  [{check_id}] {len(entries)} files ({pct:.0f}%) — e.g. {entries[0].file}")
            for entry in entries[:MAX_SHOWN_PER_CHECK]:
                lines.append(f"      {entry.file}: {entry.reason}")
            if len(entries) > MAX_SHOWN_PER_CHECK:
                lines.append(f"      ... showing first {MAX_SHOWN_PER_CHECK} of {len(entries)}")
        lines.append("")

    lines.append("─" * 40)
    dim_line = " · ".join(f"{dim} {letter}" for dim, (_, letter) in grades.items())
    lines.append(f"Per-dimension: {dim_line}")
    return "\n".join(lines)


VAULT_MARKERS = (".vault-meta.json", "decisions", "sessions")


def looks_like_a_vault(path: Path) -> bool:
    """True when the directory is a tolvi vault that simply has no notes yet."""
    return any((path / marker).exists() for marker in VAULT_MARKERS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="tolvi-format vault health check")
    parser.add_argument("vault_dir", type=Path)
    args = parser.parse_args(argv)

    if not args.vault_dir.is_dir():
        print(f"error: {args.vault_dir} is not a directory", file=sys.stderr)
        return 1

    notes = load_notes(args.vault_dir)
    if not notes:
        # A freshly provisioned vault holds only `templates/`, which the loader
        # skips. That is a valid state, not an error — but the same emptiness
        # also shows when the path points at a repo root instead of its vault/,
        # so only the former is reported as healthy.
        if looks_like_a_vault(args.vault_dir):
            print(f"VAULT HEALTH — {args.vault_dir}")
            print("─" * 40)
            print("No notes yet — nothing to check. Vault structure looks correct.")
            return 0
        print(f"error: no markdown files found under {args.vault_dir}", file=sys.stderr)
        print("hint: pass the `vault/` directory itself, not the repo root that contains it", file=sys.stderr)
        return 1

    print(render_report(args.vault_dir, notes, run_all_checks(notes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
