# Engineer pack

Templates for software engineers. Covers the four decision categories that come up most often in day-to-day engineering work, plus a pattern template and session log.

## Templates

| File | Use when |
|---|---|
| `decision.md` | Generic starting point for any decision |
| `decision-tech.md` | Choosing a language, framework, library, or tool |
| `decision-arch.md` | Structural / architectural choices |
| `decision-dep.md` | Adding, removing, or pinning a dependency |
| `decision-process.md` | CI/CD, branching strategy, testing approach, workflow |
| `pattern.md` | A reusable approach worth naming |
| `session.md` | What happened in a work session |

## Decision categories

**Tech choices** (`decision-tech.md`) are the most common: "use Postgres not MySQL", "pick Vite over webpack", "write this in Go". The key question is always the same: why this over the alternatives, and what did you accept by choosing it.

**Architecture decisions** (`decision-arch.md`) are harder to reverse and more important to document: how data flows, where boundaries live, what the system will not do.

**Dependency decisions** (`decision-dep.md`) matter more than they seem. When you add a package you're accepting its maintenance burden, license, and security surface. Worth a 3-line note even for small packages.

**Process decisions** (`decision-process.md`) are the easiest to forget and the most confusing when you pick up a repo six months later. Branch strategy, test philosophy, and deploy approach belong here.

## Naming conventions

Decisions: `YYYY-MM-DD-slug.md` — date-prefixed, kebab-case slug derived from the title.

Patterns: `slug.md` — no date prefix. Patterns are timeless; decisions are time-stamped.

Sessions: `YYYY-MM-DD.md` — one file per day, multiple session blocks per file if you work multiple sessions.
