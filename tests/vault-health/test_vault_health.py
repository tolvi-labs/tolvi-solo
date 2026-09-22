from datetime import date
from pathlib import Path

import pytest

from vault_health import (
    DIMENSIONS,
    KNOWN_STATUSES,
    check_duplicate_titles,
    check_empty_tags,
    check_status_enum,
    check_template_placeholder,
    check_unicode_escaping,
    check_unparseable,
    compute_grades,
    extract_heading,
    is_skipped,
    load_notes,
    main,
    parse_frontmatter,
    render_report,
    run_all_checks,
)

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "vault-health" / "scripts" / "vault_health.py"


def write(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def note(frontmatter: str, body: str = "# A title\n\nsome prose\n") -> str:
    return f"---\n{frontmatter}\n---\n{body}"


GOOD = note("tags: [decision, demo]\ndate: 2026-01-01\nstatus: active\n")


# --- loader -------------------------------------------------------------

def test_load_notes_parses_frontmatter_and_body(tmp_path):
    write(tmp_path, "decisions/a.md", GOOD)
    (n,) = load_notes(tmp_path)
    assert n.rel_path == "decisions/a.md"
    assert n.frontmatter["tags"] == ["decision", "demo"]
    assert "some prose" in n.body
    assert n.parse_error is None


@pytest.mark.parametrize("rel,skipped", [
    ("templates/decision.md", True),
    ("vault/templates/decision.md", True),
    ("decisions/a.md", False),
    ("decisions/templates-i-considered.md", False),
])
def test_is_skipped_matches_path_segments_not_prefixes(rel, skipped):
    assert is_skipped(rel) is skipped


def test_load_notes_skips_templates_one_level_up(tmp_path):
    """Pointed a level above the vault, `vault/templates/` must still skip."""
    write(tmp_path, "vault/templates/decision.md", note("tags: [x]\ndate: YYYY-MM-DD\n"))
    write(tmp_path, "vault/decisions/a.md", GOOD)
    assert [n.rel_path for n in load_notes(tmp_path)] == ["vault/decisions/a.md"]


def test_load_notes_skips_templates_dir(tmp_path):
    write(tmp_path, "templates/decision.md", note("tags: [decision, <repo-slug>]\ndate: YYYY-MM-DD\n"))
    write(tmp_path, "decisions/a.md", GOOD)
    assert [n.rel_path for n in load_notes(tmp_path)] == ["decisions/a.md"]


def test_load_notes_records_missing_frontmatter_as_parse_error(tmp_path):
    write(tmp_path, "a.md", "# no frontmatter here\n")
    (n,) = load_notes(tmp_path)
    assert n.frontmatter is None
    assert n.parse_error == "no frontmatter block found"


def test_load_notes_records_bad_yaml_as_parse_error(tmp_path):
    write(tmp_path, "a.md", note("tags: [unclosed\n"))
    (n,) = load_notes(tmp_path)
    assert n.frontmatter is None
    assert n.parse_error is not None


def test_load_notes_records_non_mapping_frontmatter_as_parse_error(tmp_path):
    write(tmp_path, "a.md", note("- just\n- a list\n"))
    (n,) = load_notes(tmp_path)
    assert n.parse_error == "frontmatter is not a mapping"


# --- frontmatter parser -------------------------------------------------
#
# Expected values are what yaml.v3 (the Go port's parser) and PyYAML both
# produce for the same input, so parity holds on every shape accepted here.

@pytest.mark.parametrize("text,expected", [
    ("date: 2026-01-01", {"date": "2026-01-01"}),
    ("tags: [decision, demo]", {"tags": ["decision", "demo"]}),
    ("tags: []", {"tags": []}),
    ('tags: ["a, b", \'c\']', {"tags": ["a, b", "c"]}),
    ('date: "2026-09-15"', {"date": "2026-09-15"}),
    ("date: '2026-08-08'", {"date": "2026-08-08"}),
    ("title: 'it''s'", {"title": "it's"}),
    ('title: "a \\"q\\" \\u00e9"', {"title": 'a "q" é'}),
    ("source: https://x.y/z", {"source": "https://x.y/z"}),
    ("title: C#sharp", {"title": "C#sharp"}),
    ("tags: [a] # why\nstatus: active # note", {"tags": ["a"], "status": "active"}),
    ("my key: v", {"my key": "v"}),
    ('"k": v', {"k": "v"}),
    ("tags:\n  - a\n  - b", {"tags": ["a", "b"]}),
    ("tags:\n- a\n- b\nstatus: active", {"tags": ["a", "b"], "status": "active"}),
    ("metadata:\n  type: decision\n  deep:\n    x: y\nstatus: active",
     {"metadata": {"type": "decision", "deep": {"x": "y"}}, "status": "active"}),
    ("tags: [a,\n  b]", {"tags": ["a", "b"]}),
    ("tags:\n  [\n    a,\n    b(c),\n  ]\nstatus: active", {"tags": ["a", "b(c)"], "status": "active"}),
    ("m: {a: b, c: [d]}", {"m": {"a": "b", "c": ["d"]}}),
    ("tags: [[a]]", {"tags": [["a"]]}),
    ("summary: |\n  one\n  two\nstatus: active", {"summary": "one\ntwo\n", "status": "active"}),
    ("tags: [a]\nsummary: |\n  hi", {"tags": ["a"], "summary": "hi"}),  # the block ends the input
    ("tags: [a]\ntags: [b]", {"tags": ["b"]}),
    ("# a comment\n\ntags: [a]", {"tags": ["a"]}),
])
def test_parse_frontmatter_accepts_what_yaml_accepts(text, expected):
    assert parse_frontmatter(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("status:", None),
    ("status: ~", None),
    ("status: null", None),
    ("flag: true", True),
    ("flag: False", False),
    ("n: 3", 3),
])
def test_parse_frontmatter_resolves_scalars(text, expected):
    (value,) = parse_frontmatter(text).values()
    assert value == expected and type(value) is type(expected)


@pytest.mark.parametrize("text", [
    "title: Foo: bar",          # mapping value inside a plain scalar
    "title: foo:",
    "x: - foo",                 # block entry where a value belongs
    "x: `foo`",
    "x: @foo",
    "x: *foo",                  # alias
    "tags: [a]\nmetadata:\n\ttype: x",   # tab indentation
    "tags: [a]\n  status: active",       # indentation with no parent
    "tags: [unclosed",
    "tags: [a] x",
])
def test_parse_frontmatter_rejects_what_yaml_rejects(text):
    with pytest.raises(ValueError):
        parse_frontmatter(text)


@pytest.mark.parametrize("text", [
    "tags: &x [a]",             # anchor
    "tags: !!seq [a]",          # explicit tag
    "tags: [a]\n...",           # document end marker
])
def test_parse_frontmatter_refuses_unsupported_yaml_loudly(text):
    with pytest.raises(ValueError, match="unsupported"):
        parse_frontmatter(text)


@pytest.mark.parametrize("text", ["", "hello", "- just\n- a list"])
def test_parse_frontmatter_requires_a_mapping(text):
    with pytest.raises(ValueError, match="frontmatter is not a mapping"):
        parse_frontmatter(text)


def test_script_imports_only_the_standard_library():
    """The packaged skill cannot carry a pip dependency, so none may creep back."""
    import ast
    import sys

    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = {
        (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported <= set(sys.stdlib_module_names) | {"__future__"}


def test_script_names_its_interpreter():
    assert SCRIPT.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3\n")


# --- heading extraction -------------------------------------------------

@pytest.mark.parametrize("body,expected", [
    ("# Plain title\n", "Plain title"),
    ("\n\n# Later title\n\ntext\n", "Later title"),
    ("## Not h1\n# Real one\n", "Real one"),
    ("no heading at all\n", ""),
    ("#NoSpace\n", ""),
])
def test_extract_heading(body, expected):
    assert extract_heading(body) == expected


# --- empty-tags ---------------------------------------------------------

def test_empty_tags_flags_missing_and_empty(tmp_path):
    write(tmp_path, "a.md", note("date: 2026-01-01\n"))
    write(tmp_path, "b.md", note("tags: []\ndate: 2026-01-01\n"))
    write(tmp_path, "c.md", GOOD)
    flagged = {f.file for f in check_empty_tags(load_notes(tmp_path))}
    assert flagged == {"a.md", "b.md"}


def test_empty_tags_skips_unparseable(tmp_path):
    write(tmp_path, "a.md", "no frontmatter\n")
    assert check_empty_tags(load_notes(tmp_path)) == []


# --- status-enum --------------------------------------------------------

def test_status_enum_accepts_the_tolvi_vocabulary(tmp_path):
    for i, status in enumerate(sorted(KNOWN_STATUSES)):
        write(tmp_path, f"{i}.md", note(f"tags: [x]\nstatus: {status}\n"))
    assert check_status_enum(load_notes(tmp_path)) == []


def test_status_enum_flags_unknown_value(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\nstatus: archived\n"))
    (f,) = check_status_enum(load_notes(tmp_path))
    assert f.check_id == "status-enum" and "archived" in f.reason


def test_status_enum_treats_absent_status_as_active(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\ndate: 2026-01-01\n"))
    assert check_status_enum(load_notes(tmp_path)) == []


# --- duplicate-title ----------------------------------------------------

def test_duplicate_titles_matches_on_body_heading_not_frontmatter(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\n", "# Same Title\n"))
    write(tmp_path, "b.md", note("tags: [x]\n", "# same   title\n"))
    write(tmp_path, "c.md", note("tags: [x]\n", "# Different\n"))
    flagged = {f.file for f in check_duplicate_titles(load_notes(tmp_path))}
    assert flagged == {"a.md", "b.md"}


def test_duplicate_titles_ignores_notes_without_a_heading(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\n", "no heading\n"))
    write(tmp_path, "b.md", note("tags: [x]\n", "also none\n"))
    assert check_duplicate_titles(load_notes(tmp_path)) == []


# --- template-placeholder -----------------------------------------------

def test_template_placeholder_flags_unfilled_frontmatter(tmp_path):
    write(tmp_path, "a.md", note("tags: [decision, <venture-slug>]\ndate: YYYY-MM-DD\n"))
    (f,) = check_template_placeholder(load_notes(tmp_path))
    assert f.check_id == "template-placeholder"
    assert "slug" in f.reason and "date" in f.reason


def test_template_placeholder_flags_unfilled_session_heading(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\n", "## [HH:MM] Session, a thing\n"))
    (f,) = check_template_placeholder(load_notes(tmp_path))
    assert "time" in f.reason


def test_template_placeholder_ignores_naming_convention_prose(tmp_path):
    """A note documenting `sessions/YYYY-MM-DD.md` is prose, not a half-filled template."""
    body = "# Real title\n\nblocks the commit if no `vault/sessions/YYYY-MM-DD.md` exists\n"
    write(tmp_path, "a.md", note("tags: [x]\ndate: 2026-06-05\nstatus: active\n", body))
    assert check_template_placeholder(load_notes(tmp_path)) == []


def test_template_placeholder_ignores_slug_mention_in_prose(tmp_path):
    body = "# Real title\n\nthe `<repo-slug>` token is substituted at install time\n"
    write(tmp_path, "a.md", note("tags: [x]\ndate: 2026-06-05\n", body))
    assert check_template_placeholder(load_notes(tmp_path)) == []


@pytest.mark.parametrize("frontmatter", [
    "tags: [x]\ndate: 2026-01-01\n",
    "tags: [x]\nnote: an <br> tag\n",
])
def test_template_placeholder_does_not_false_positive(tmp_path, frontmatter):
    write(tmp_path, "a.md", note(frontmatter))
    assert check_template_placeholder(load_notes(tmp_path)) == []


# --- unicode-escaping ---------------------------------------------------

def test_unicode_escaping_flags_escaped_sequences(tmp_path):
    write(tmp_path, "a.md", note("tags: [x]\n", "# T\n\nliteral \\u2014 dash\n"))
    (f,) = check_unicode_escaping(load_notes(tmp_path))
    assert f.severity == "low" and "\\u2014" in f.reason


def test_unicode_escaping_skips_unparseable(tmp_path):
    write(tmp_path, "a.md", "no frontmatter \\u2014\n")
    assert check_unicode_escaping(load_notes(tmp_path)) == []


# --- unparseable + grading ---------------------------------------------

def test_unparseable_reported_once_per_file(tmp_path):
    write(tmp_path, "a.md", "no frontmatter\n")
    (f,) = check_unparseable(load_notes(tmp_path))
    assert f.check_id == "unparseable-frontmatter"


def test_unparseable_excluded_from_grade_denominator(tmp_path):
    write(tmp_path, "good.md", GOOD)
    write(tmp_path, "bad.md", "no frontmatter\n")
    notes = load_notes(tmp_path)
    grades, (overall_pct, letter) = compute_grades(notes, run_all_checks(notes))
    assert overall_pct == 100.0 and letter == "A+"


def test_grades_drop_when_a_dimension_is_affected(tmp_path):
    write(tmp_path, "a.md", note("date: 2026-01-01\n"))  # no tags
    write(tmp_path, "b.md", GOOD)
    notes = load_notes(tmp_path)
    grades, _ = compute_grades(notes, run_all_checks(notes))
    assert grades["tags"][0] == 50.0
    assert grades["unicode"][0] == 100.0


def test_empty_vault_grades_as_perfect():
    grades, (pct, letter) = compute_grades([], [])
    assert pct == 100.0 and letter == "A+"


# --- integration --------------------------------------------------------

def test_run_all_checks_covers_every_dimension(tmp_path):
    write(tmp_path, "a.md", note("date: 2026-01-01\n", "# Dup\n"))          # empty-tags
    write(tmp_path, "b.md", note("tags: [x]\nstatus: bogus\n", "# Dup\n"))  # status + dup
    write(tmp_path, "c.md", note("tags: [x]\ndate: YYYY-MM-DD\n"))          # placeholder
    write(tmp_path, "d.md", note("tags: [x]\n", "# U\n\n\\u2014\n"))        # unicode
    ids = {f.check_id for f in run_all_checks(load_notes(tmp_path))}
    assert ids == {"empty-tags", "status-enum", "duplicate-title", "template-placeholder", "unicode-escaping"}
    covered = set().union(*DIMENSIONS.values())
    assert covered == ids


def test_render_report_is_readable(tmp_path):
    write(tmp_path, "a.md", note("date: 2026-01-01\n"))
    notes = load_notes(tmp_path)
    out = render_report(tmp_path, notes, run_all_checks(notes))
    assert "VAULT HEALTH" in out
    assert "Files scanned: 1" in out
    assert "[empty-tags]" in out
    assert "Per-dimension:" in out


def test_render_report_truncates_long_finding_lists(tmp_path):
    for i in range(15):
        write(tmp_path, f"{i}.md", note("date: 2026-01-01\n"))
    notes = load_notes(tmp_path)
    out = render_report(tmp_path, notes, run_all_checks(notes))
    assert "showing first 10 of 15" in out


# --- empty-vault handling ----------------------------------------------

def test_fresh_vault_with_only_templates_is_healthy_not_an_error(tmp_path, capsys):
    """A just-provisioned vault holds only templates/ — a valid state, exit 0."""
    write(tmp_path, "templates/decision.md", note("tags: [decision, <repo-slug>]\ndate: YYYY-MM-DD\n"))
    (tmp_path / ".vault-meta.json").write_text('{"pack": "data"}', encoding="utf-8")
    assert main([str(tmp_path)]) == 0
    assert "No notes yet" in capsys.readouterr().out


def test_vault_with_standard_dirs_but_no_notes_is_healthy(tmp_path, capsys):
    for d in ("decisions", "patterns", "sessions"):
        (tmp_path / d).mkdir()
    assert main([str(tmp_path)]) == 0
    assert "No notes yet" in capsys.readouterr().out


def test_non_vault_directory_with_no_markdown_is_still_an_error(tmp_path, capsys):
    (tmp_path / "src").mkdir()
    assert main([str(tmp_path)]) == 1
    assert "not the repo root" in capsys.readouterr().err
