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
    load_notes,
    render_report,
    run_all_checks,
)


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
