---
tags: [decision, tolvi-solo]
date: 2026-09-12
repo: tolvi-solo
status: active
ticket: none
user_impact: none
product_area: Schema
---

# Packs handling sensitive material record posture, never payload

**Date:** 2026-09-12
**Repo:** tolvi-solo

## Why
A tolvi vault is plain Markdown in a git repository and the whole premise is that it gets committed. That is right for reasoning and wrong for client identities, personal data, and exploitable detail. Three packs now need a confidentiality story, and answering it per-pack would have produced three inconsistent conventions. The rule has to be uniform because the failure mode is uniform: a repository that is cloned, backed up, or made public carries whatever the vault holds.

## How
The same discipline appears in each pack in the key that pack needs, and every affected template repeats it as a trailing blockquote so it stays in view while writing rather than living only in a README nobody re-reads.

- **CPA** — an opaque `client:` code, never a name, with the code-to-client mapping kept outside the vault. No EINs, SSNs, account numbers, or dollar figures.
- **Data** — `decision-dataset.md` records PII *posture* (what the data contains, what was removed or hashed, what that implies about where it may live) and never sample records or identifiers.
- **Security** — notes record the triage decision and reference an internal tracker id for specifics. No working reproductions, payloads, credentials, or unpatched detail for an exposed system.
- **Entrepreneur** — `decision-hire.md` refers to people by role or candidate code, since hiring notes record judgements about real people.
- The reasoning survives redaction intact, which is what makes the rule cheap to follow. A vuln note saying the finding was an authz bypass, rated high but unreachable from the internet behind a VPN gate, deferred a cycle with that gate as the compensating control, is as useful in two years as the version containing a working request and carries none of the liability.
- **Rejected — gitignoring the vault for sensitive roles:** it would make those packs second-class and break the committable, agent-readable premise the product rests on.
- **Rejected — a `confidential: yes|no` flag per note:** it puts the judgement on the user at every write and designs nothing out, where a pseudonymous key and a posture-only rule remove the sensitive material at the source.

## Outcome
Four packs share one confidentiality rule expressed in four keys, stated in each pack README and repeated at the foot of every template that touches sensitive material.
