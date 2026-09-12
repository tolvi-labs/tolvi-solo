---
tags: [decision, tolvi-solo]
date: 2026-09-12
repo: tolvi-solo
status: active
ticket: none
user_impact: none
product_area: Schema
---

# Reproducibility is frontmatter on a result, not its own decision category

**Date:** 2026-09-12
**Repo:** tolvi-solo

## Why
The Data pack's advertised verticals listed reproducibility alongside experiments, datasets, and model rationale, which implied a fourth decision template. Writing one would have produced a document nobody has a reason to create: "we decided to be reproducible" is a statement of intent, not a decision with alternatives and a trade-off. What people actually need is the ability to re-run *one specific result* months later, and that is metadata belonging to that result.

## How
- `decision-experiment.md` carries `seed` and `commit` in frontmatter plus a **Reproducibility** bullet in its How block covering environment and where run artifacts live. Reproducibility travels with the run it describes.
- No `decision-repro.md` template exists, and the Data pack README states the reasoning so a contributor does not add one as an apparent omission.
- The same test applied elsewhere in the pack: PII posture is a field on `decision-dataset.md` rather than a privacy template, and serving shape is a field on `decision-model.md` rather than a deployment template.
- **Rejected — a fourth `decision-repro.md` template:** it would either duplicate the experiment note's frontmatter or sit empty, and a template that is never filled in is worse than no template because it reads as a gap in the vault rather than a deliberate choice.
- **Rejected — a top-level `repro:` key on every Data decision:** dataset and model decisions are not runs and have nothing to reproduce, so the key would be `none` on two thirds of the pack.

## Outcome
The Data pack ships three decision categories, not four, with reproducibility as frontmatter on the only category where it means anything.
