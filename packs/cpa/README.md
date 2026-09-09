# CPA pack

Templates for accountants in solo or small practice. Covers the judgement calls that a workpaper records only as a number, plus a workflow pattern template and session log. The return shows the position you took. The vault carries why it was defensible, what else you considered, and what the client was told.

## Confidentiality — read this first

This vault is plain Markdown in a git repository, and it is designed to be committed. That is fine for the reasoning; it is not fine for client data.

**Use an opaque client code everywhere — never a name.** Keep the code-to-client mapping outside the vault, in whatever system already holds client records. Nothing goes in the vault that you would not want in a repository backup: no names, no EINs or SSNs, no account numbers, no addresses, no dollar figures. Every template in this pack repeats the rule at the bottom so it stays in view while you write.

The reasoning survives redaction perfectly well. "Client `mh-042`, 2025, treated the equipment purchase as a §179 deduction rather than bonus depreciation because of the state add-back" is exactly as useful to you in two years as the version with a name and a number in it, and it carries none of the risk.

## Templates

| File | Use when |
|---|---|
| `decision.md` | Generic starting point for any client decision |
| `decision-position.md` | A tax or accounting treatment that required judgement |
| `decision-engagement.md` | Accepting, declining, rescoping, or withdrawing from work |
| `decision-compliance.md` | A filing, election, or reporting obligation |
| `pattern.md` | A reusable workflow worth naming |
| `session.md` | What happened in a work session |

## Decision categories

**Positions** (`decision-position.md`) are the heart of a CPA's vault, the way editorial decisions are a writer's. A workpaper records the treatment; it rarely records why the alternative was rejected, how strong the support actually was, or what the client was told about the risk. That reasoning is what you need years later when the position is questioned and the engagement is cold — and reconstructing it from memory is exactly what you do not want to be doing at that point. The template asks for the authority relied on and the point where the position is weakest, because the weak point is the part you will be asked about.

**Engagement decisions** (`decision-engagement.md`) are worth recording most when the answer is no. A declined client, a scope you refused to expand, a withdrawal mid-engagement: each one has a reason that matters if it comes back around, and a paper trail that helps if it becomes contentious. Independence and conflict checks belong here too, recorded at the time rather than reconstructed.

**Compliance notes** (`decision-compliance.md`) cover obligations that needed a decision rather than routine handling — a first-year filing, a changed fact pattern, an extension posture, a missed deadline being cured. The `due` and `filed` frontmatter keys make the open ones easy to filter, and the template asks where proof of filing is retained, since that evidence itself must live outside the vault.

**Workflow patterns** (`pattern.md`) carry the reusable half of a practice: the onboarding sequence that catches problems early, the triage order that survives extension season, the question that resolves a recurring ambiguity fastest. These are timeless and client-independent, which makes them the one part of the vault that carries no confidentiality burden at all.

## Naming conventions

Decisions: `YYYY-MM-DD-slug.md` — date-prefixed, kebab-case slug derived from the title. Use the client code in the slug, not the client name.

Patterns: `slug.md` — no date prefix. Patterns are timeless; decisions are time-stamped.

Sessions: `YYYY-MM-DD.md` — one file per day, multiple session blocks per file if you work in more than one sitting.
