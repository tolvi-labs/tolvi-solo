# Security pack

Templates for security engineers and solo practitioners. Covers the judgement calls that a scanner report and a closed ticket never capture, plus a pattern template and session log. A fixed finding shows what you changed. The vault carries why you rated it that way, what you decided not to defend against, and what a control does not cover.

## What does not go in this vault — read this first

This vault is plain Markdown in a git repository, and it is designed to be committed. That is right for decisions and rationale. It is wrong for anything exploitable.

**Record the decision, not the exploit.** No working reproduction steps, no payloads, no credentials or tokens, no unpatched specifics for a system still exposed, no customer or reporter identities. Those belong in whatever tracker already holds them, referenced from the note by id. Every template repeats the rule at the bottom so it stays in view while you write.

The reasoning survives that redaction intact. "Finding class was an authz bypass on an internal admin route, rated high but not reachable from the internet because the route sits behind the VPN gate, so it was deferred to the next cycle with the gate as the compensating control, tracked as `SEC-214`" is exactly as useful in two years as the version containing a working request — and it does not turn your repository into a liability if it is ever cloned, leaked, or made public.

## Templates

| File | Use when |
|---|---|
| `decision.md` | Generic starting point for any security decision |
| `decision-threat-model.md` | Deciding what a system defends against, and what it does not |
| `decision-vuln.md` | Triaging a finding: fix, accept, or defer |
| `decision-control.md` | Adopting, replacing, or removing a control |
| `pattern.md` | A reusable review approach worth naming |
| `session.md` | What happened in a work session |

## Decision categories

**Threat models** (`decision-threat-model.md`) are the pack's centre of gravity. The template asks for the asset rather than the technology, because a model that covers everything covers nothing, and it insists on what is *explicitly out of scope*. That exclusion list is the most valuable and most frequently unwritten part of a threat model: it is what tells a future reader that you considered the malicious insider and chose not to defend against them, rather than that you never thought about it. Accepted risks and who accepted them belong here too, along with a review date, since a threat model goes stale as the system grows.

**Vulnerability triage** (`decision-vuln.md`) records a decision, not a finding. The scanner already has the finding. What disappears is the reasoning: whether the vulnerable path was actually reachable in this deployment, what gated it, why a high severity was deferred anyway, and what compensating control covered the gap in the meantime. The technical reproduction stays in the tracker, referenced by id.

**Controls** (`decision-control.md`) have one field that justifies the whole template: what the control does **not** mitigate. Controls accumulate assumed coverage — a WAF that people believe stops logic flaws, an audit log nobody reads, an allowlist with a wildcard. Writing down the gap at the moment you install the control is the only reliable time to write it down. The template also asks how the control is verified rather than assumed, and whether it fails closed or open.

## Naming conventions

Decisions: `YYYY-MM-DD-slug.md` — date-prefixed, kebab-case slug derived from the title. Use the finding class or system in the slug, never a live vulnerability detail.

Patterns: `slug.md` — no date prefix. Patterns are timeless; decisions are time-stamped.

Sessions: `YYYY-MM-DD.md` — one file per day, multiple session blocks per file if you work in more than one sitting.
