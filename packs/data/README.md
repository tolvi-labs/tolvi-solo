# Data pack

Templates for data scientists, analysts, and ML engineers working alone. Covers the decisions that a notebook records only as a number, plus a pattern template and session log. A run's output tells you what happened. The vault carries what you were testing, what the result ruled out, and what you excluded from the data on purpose.

## Templates

| File | Use when |
|---|---|
| `decision.md` | Generic starting point for any data decision |
| `decision-experiment.md` | Running something whose result should change what you do next |
| `decision-dataset.md` | Adopting, rebuilding, or retiring a dataset |
| `decision-model.md` | Choosing an approach, architecture, or serving shape |
| `pattern.md` | A reusable method worth naming |
| `session.md` | What happened in a work session |

## Decision categories

**Experiments** (`decision-experiment.md`) are the heart of a data vault. The template asks for a hypothesis stated so that the run could contradict it, because an experiment you cannot lose teaches nothing. It also asks what the result kills — the approach, parameter, or belief you can now stop revisiting. That line is the whole point: without it you re-run the same dead end in four months, having forgotten that you already answered it.

**Datasets** (`decision-dataset.md`) carry the decisions that explain a model's behaviour long after the model is built. Provenance and licence matter, but the field that earns its place is what you excluded on purpose — the classes, sources, or time ranges you dropped. Those exclusions are invisible in the trained artifact and are usually the explanation when someone later asks why the model is blind to something. PII posture is recorded here too: what the data contains, what was removed, and what that implies about where it may live.

**Models** (`decision-model.md`) are where the interesting content is the trade-off, not the choice. Almost any approach can be made to work; what you want recorded is the baseline it actually beat, the constraint that ruled out the obvious option, and what you gave up — interpretability, tail accuracy, inference cost, or retraining burden. The template also asks what you are *not* claiming it does.

## Reproducibility

There is no reproducibility template, on purpose. "We decided to be reproducible" is not a decision; being able to re-run one specific result is metadata about that result. So `decision-experiment.md` carries `seed`, `commit`, and a reproducibility bullet in its How block, and reproducibility travels with the run it belongs to rather than sitting in a document of its own.

## Naming conventions

Decisions: `YYYY-MM-DD-slug.md` — date-prefixed, kebab-case slug derived from the title.

Patterns: `slug.md` — no date prefix. Patterns are timeless; decisions are time-stamped.

Sessions: `YYYY-MM-DD.md` — one file per day, multiple session blocks per file if you work in more than one sitting.
