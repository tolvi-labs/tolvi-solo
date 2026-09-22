#!/usr/bin/env python3
"""Deterministic health checks for a tolvi-format vault.

Checks only what the tolvi-format-v1 schema actually defines — frontmatter
`tags` and `status`, the `# Heading` a note opens with, and unfilled template
placeholders. `related:` and wikilinks are deliberately never checked.

Files under `templates/` are skipped: they are unfilled by design.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

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


# Frontmatter is parsed with the standard library rather than PyYAML, so the
# script has nothing to install and packages self-contained. It covers the
# YAML that vault frontmatter uses, and on every shape it covers it accepts
# and rejects the same input as yaml.v3, the parser behind the Go port in the
# tolvi CLI, which keeps the two implementations' findings in parity. Anchors,
# aliases, explicit tags and document markers are refused as unsupported
# rather than guessed at.

_NULLS = frozenset({"", "~", "null", "Null", "NULL"})
_BOOLS = {"true": True, "True": True, "TRUE": True, "false": False, "False": False, "FALSE": False}
_INT_RE = re.compile(r"[-+]?[0-9]+\Z")
_KEY_RE = re.compile(
    r"""("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s:#&*!|>%@`'"\[\]{},?-][^:]*?|-[^\s:][^:]*?):(?:[ \t]+(.*))?\Z"""
)
_BLOCK_HEADER_RE = re.compile(r"[|>](?:[-+]?[1-9]?|[1-9][-+])\Z")


def _unsupported(what: str) -> ValueError:
    return ValueError(f"unsupported YAML in frontmatter: {what}")


def _opens_quote(text: str, i: int) -> bool:
    """A quote opens a quoted scalar only where a token starts, so `it's` stays plain."""
    return text[i] in "\"'" and (i == 0 or text[i - 1] in " \t[{,:")


def _scan(text: str):
    """Yield (index, char, inside_quotes) for each character."""
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            yield i, ch, True
            if ch == "\\" and quote == '"':
                i += 1
            elif ch == quote:
                if quote == "'" and text[i + 1:i + 2] == "'":
                    i += 1
                else:
                    quote = None
        elif _opens_quote(text, i):
            quote = ch
            yield i, ch, True
        else:
            yield i, ch, False
        i += 1


def _strip_comment(text: str) -> str:
    for i, ch, quoted in _scan(text):
        if ch == "#" and not quoted and (i == 0 or text[i - 1] in " \t"):
            return text[:i]
    return text


def _flow_depth(text: str) -> int:
    depth = 0
    for _, ch, quoted in _scan(text):
        if not quoted:
            depth += (ch in "[{") - (ch in "]}")
    return depth


def _quoted(text: str, pos: int) -> tuple[str, int]:
    """Parse the quoted scalar starting at `pos`; return it and the index after it."""
    quote = text[pos]
    i = pos + 1
    while i < len(text):
        if quote == '"' and text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            if quote == "'" and text[i + 1:i + 2] == "'":
                i += 2
                continue
            raw = text[pos:i + 1]
            if quote == "'":
                return raw[1:-1].replace("''", "'"), i + 1
            try:
                return json.loads(raw, strict=False), i + 1
            except json.JSONDecodeError:
                raise _unsupported("an escape sequence JSON does not share") from None
        i += 1
    raise ValueError("unclosed quoted scalar (multi-line quoted scalars are unsupported)")


def _plain(text: str, flow: bool):
    text = text.strip()
    if not text:
        return None
    first = text[0]
    if first == "&":
        raise _unsupported("anchors")
    if first == "*":
        raise _unsupported("aliases")
    if first == "!":
        raise _unsupported("explicit tags")
    if first in "@`%" or (flow and first in "|>"):
        raise ValueError(f"character {first!r} cannot start a plain scalar")
    if text == "-" or text.startswith("- "):
        raise ValueError("block sequence entries are not allowed here")
    if text == "?" or text.startswith("? "):
        raise _unsupported("complex keys")
    if ": " in text or text.endswith(":"):
        if flow:
            raise _unsupported("single-pair mappings inside flow collections")
        raise ValueError("mapping values are not allowed here")
    if text in _NULLS:
        return None
    if text in _BOOLS:
        return _BOOLS[text]
    if _INT_RE.match(text):
        return int(text)
    return text


def _skip_space(text: str, pos: int) -> int:
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    return pos


def _flow(text: str, pos: int):
    """Parse the flow value starting at `pos`; return it and the index after it."""
    pos = _skip_space(text, pos)
    if pos >= len(text):
        raise ValueError("unclosed flow collection")
    if text[pos] in "\"'":
        return _quoted(text, pos)
    if text[pos] not in "[{":
        end = pos
        while end < len(text) and text[end] not in ",[]{}":
            end += 1
        return _plain(text[pos:end], flow=True), end

    closer = "]" if text[pos] == "[" else "}"
    items: list | dict = [] if closer == "]" else {}
    pos += 1
    while True:
        pos = _skip_space(text, pos)
        if pos >= len(text):
            raise ValueError("unclosed flow collection")
        if text[pos] == closer:
            return items, pos + 1
        if closer == "]":
            item, pos = _flow(text, pos)
            items.append(item)
        else:
            if text[pos] in "\"'":
                key, pos = _quoted(text, pos)
            else:
                end = pos
                while end < len(text) and text[end] not in ",:{}[]":
                    end += 1
                key, pos = text[pos:end].strip(), end
            pos = _skip_space(text, pos)
            value = None
            if pos < len(text) and text[pos] == ":":
                value, pos = _flow(text, pos + 1)
            items[key] = value
        pos = _skip_space(text, pos)
        if pos < len(text) and text[pos] == ",":
            pos += 1
        elif pos >= len(text) or text[pos] != closer:
            raise ValueError(f"expected ',' or '{closer}' in flow collection")


class _FrontmatterParser:
    def __init__(self, text: str):
        self.lines = text.split("\n")
        self.i = 0

    def fail(self, message: str, line: int | None = None) -> ValueError:
        return ValueError(f"frontmatter line {(self.i if line is None else line) + 1}: {message}")

    def peek(self) -> tuple[int, str] | None:
        """The indent and content of the next line that carries content."""
        while self.i < len(self.lines):
            line = self.lines[self.i].rstrip()
            content = line.lstrip(" ")
            if not content or content.startswith("#"):
                self.i += 1
                continue
            if content[0] == "\t":
                raise self.fail("tabs cannot indent YAML")
            if content in ("---", "...") or content.startswith(("--- ", "... ")):
                raise _unsupported("document markers")
            return len(line) - len(content), content
        return None

    def mapping(self, indent: int) -> dict:
        result = {}
        while (nxt := self.peek()) is not None:
            ind, content = nxt
            if ind < indent:
                break
            if ind > indent:
                raise self.fail("unexpected indentation")
            match = _KEY_RE.match(content)
            if not match:
                raise self.fail("expected 'key: value'")
            raw_key = match.group(1)
            key = _quoted(raw_key, 0)[0] if raw_key[0] in "\"'" else raw_key.strip()
            line = self.i
            self.i += 1
            try:
                result[key] = self.value(match.group(2) or "", indent)
            except ValueError as exc:
                if str(exc).startswith("frontmatter line"):
                    raise
                raise self.fail(str(exc), line) from None
        return result

    def sequence(self, indent: int) -> list:
        items = []
        while (nxt := self.peek()) is not None:
            ind, content = nxt
            if ind < indent or not (content == "-" or content.startswith("- ")):
                break
            if ind > indent:
                raise self.fail("unexpected indentation")
            rest = _strip_comment(content[1:]).strip()
            if _KEY_RE.match(rest):
                raise self.fail("unsupported YAML in frontmatter: mappings inside block sequences")
            if rest == "-" or rest.startswith("- "):
                raise self.fail("unsupported YAML in frontmatter: nested block sequences")
            self.i += 1
            items.append(self.value(rest, indent) if rest else None)
        return items

    def value(self, rest: str, indent: int):
        rest = _strip_comment(rest).strip()
        if not rest:
            nxt = self.peek()
            if nxt is None:
                return None
            ind, content = nxt
            is_entry = content == "-" or content.startswith("- ")
            if ind > indent:
                if is_entry:
                    return self.sequence(ind)
                if _KEY_RE.match(content):
                    return self.mapping(ind)
                # A value may start on the next, deeper line, like a flow list.
                self.i += 1
                return self.value(content, indent)
            if ind == indent and is_entry:
                return self.sequence(ind)
            return None
        if rest[0] in "[{":
            text = rest
            while _flow_depth(text) > 0:
                if self.i >= len(self.lines):
                    raise ValueError("unclosed flow collection")
                text += " " + _strip_comment(self.lines[self.i]).strip()
                self.i += 1
            value, end = _flow(text, 0)
            if text[end:].strip():
                raise ValueError("unexpected text after a flow collection")
            return value
        if rest[0] in "|>":
            return self.block_scalar(rest, indent)
        if rest[0] in "\"'":
            value, end = _quoted(rest, 0)
            if rest[end:].strip():
                raise ValueError("unexpected text after a quoted scalar")
            return value
        return _plain(rest, flow=False)

    def block_scalar(self, header: str, indent: int) -> str:
        if not _BLOCK_HEADER_RE.match(header):
            raise ValueError(f"invalid block scalar header {header!r}")
        body = []
        while self.i < len(self.lines):
            line = self.lines[self.i].rstrip()
            if line and len(line) - len(line.lstrip(" ")) <= indent:
                break
            body.append(line)
            self.i += 1
        content = [line for line in body if line]
        if not content:
            return ""
        block_indent = min(len(line) - len(line.lstrip(" ")) for line in content)
        lines = [line[block_indent:] for line in body]
        if header[0] == "|":
            text = "\n".join(lines)
        else:
            text = re.sub(r"(?<!\n)\n(?!\n)", " ", "\n".join(lines))
        # The frontmatter block carries no newline after its last line, so a
        # block scalar that ends the input has no line break to keep.
        newline = "" if self.i >= len(self.lines) and body[-1] else "\n"
        if "-" in header:
            return text.rstrip("\n")
        if "+" in header:
            return text + newline
        return text.rstrip("\n") + newline


def parse_frontmatter(text: str) -> dict:
    """Parse a frontmatter block into a mapping, or raise ValueError saying why not."""
    parser = _FrontmatterParser(text)
    first = parser.peek()
    if first is None or not _KEY_RE.match(first[1]):
        raise ValueError("frontmatter is not a mapping")
    result = parser.mapping(first[0])
    if parser.peek() is not None:
        raise parser.fail("unexpected indentation")
    return result


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
            frontmatter = parse_frontmatter(yaml_block)
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
