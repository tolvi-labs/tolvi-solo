# tolvi-solo

A vault for solo builders. Capture decisions, patterns, and session notes as plain Markdown - searchable, committable, and readable by AI agents without any server setup.

> **Status:** Early. Engineer and Writer packs are available. Entrepreneur, CPA, and more are planned.

## What it is

tolvi-solo provisions a `vault/` directory in any repo (or standalone folder) and populates it with role-specific templates. The vault is plain Markdown with YAML frontmatter - no database, no cloud, no dependencies.

Three doc types:

| Type | Where | Purpose |
|---|---|---|
| **Decisions** | `vault/decisions/` | Why you chose something over the alternatives |
| **Patterns** | `vault/patterns/` | Reusable approaches worth naming |
| **Sessions** | `vault/sessions/` | What happened, what's left open |

## Quickstart

```bash
git clone https://github.com/tolvi-labs/tolvi-solo
cd tolvi-solo
./install.sh
```

Run from inside the repo you want to vault. Creates `vault/` at the git root with the Engineer pack templates.

### With Claude Code hooks (recommended)

```bash
./install.sh --with-hooks
```

Wires two Claude Code session hooks:

- **`tolvi-recall` (SessionStart)** - surfaces recent sessions and active decisions before your first message
- **`tolvi-sync` (PreToolUse, git commit)** - fires before every commit; auto-stages vault changes and blocks the commit if no session note exists for the current branch (keyed by branch/issue, falling back to the Claude session id), so the vault is always committed alongside the code

It also installs three Claude Code slash commands (skip-if-exists, so they never clobber your own):

- **`/tolvi-recall`** - surface recent sessions and active decisions on demand
- **`/tolvi-sync`** - synthesize the whole working session into decisions, patterns, and a session log
- **`/tolvi-commit`** - run that synthesis, then stage and commit (vault + work) in one step

The hooks keep the vault committed; the `/tolvi-sync` and `/tolvi-commit` skills are what actually write the notes for you - the agent reconstructs the session and follows the schema, so you are not hand-filling templates. That synthesis is the point: it captures what was tried or considered in a working session, including reasoned rejections, which a stray Slack message or ticket never does.

### Options

```bash
./install.sh [--pack <name>] [--with-hooks] [--hooks-scope user|project]

  --pack           Schema pack to use (default: engineer)
  --with-hooks     Install Claude Code session hooks
  --hooks-scope    Where to wire hooks: user (all repos) or project (this repo only)
                   Default: user
```

## Using the vault

### With the tolvi CLI (recommended)

Install the [tolvi CLI](https://github.com/tolvi-labs/tolvi) to query your vault in plain English:

```bash
go install github.com/tolvi-labs/tolvi/cli/cmd/tolvi@latest
export ANTHROPIC_API_KEY=sk-ant-...
tolvi ask "why did we choose postgres?"
```

The CLI uses Context-Augmented Generation - whole vault into Anthropic context, streamed answer with citations.

### Without the CLI

The vault is plain Markdown. Use Claude Code, Cursor, or any editor. The session hooks work regardless of whether the CLI is installed.

### Writing decisions

Copy a template from `vault/templates/`, fill in the Why / How / Outcome sections, and save it to `vault/decisions/YYYY-MM-DD-slug.md`.

If you have the CLI:

```bash
tolvi sync decision "Choose Postgres over MySQL"
```

## Using tolvi-solo with git worktrees

The hooks resolve the vault per git working-tree, so if you run parallel agents in
`git worktree` checkouts, lay them out so each track resolves to the right vault:

- **Create worktrees as siblings, not nested.** Prefer `git worktree add ../<repo>-<issue>`
  over `git worktree add ./worktrees/<issue>`. A sibling layout keeps each track's
  tree unambiguous; a worktree nested inside the main repo invites vault resolution
  to climb into the parent repo's vault.
- **Each worktree carries its own `vault/`.** Since `vault/` is tracked, a normal
  checkout already has its own copy — the intended state. If a branch deliberately
  omits it, tolvi tells you the note is routing to a parent vault instead of failing
  silently (set `TOLVI_STRICT_WORKTREE=1` to block the commit instead of warning).
- **The vault is the shared, durable record; per-worktree notes converge via merges.**
  Notes land on their branch and reach the canonical vault when the PR merges — that's
  the design, not a leak. The leak is only a note reaching the main tree without going
  through its branch, which this convention plus per-worktree resolution prevent.
- **Sanity check before writing in a worktree:** `git rev-parse --show-toplevel`
  should equal the worktree path you think you're in. If it points at the main repo,
  you're not actually in the worktree and any note you write will route to the shared
  vault.

## Packs

| Pack | Status | Verticals |
|---|---|---|
| `engineer` | ✅ | Tech choices, architecture, dependencies, process |
| `writer` | ✅ | Projects, drafts, editorial decisions, source tracking |
| `entrepreneur` | planned | Product bets, vendor decisions, hiring, strategy |
| `cpa` | planned | Client decisions, workflow patterns, compliance notes |
| `product` | planned | Feature decisions, prioritization, specs, discovery |
| `designer` | planned | Design-system decisions, accessibility, interaction patterns, critiques |
| `consultant` | planned | Client recommendations, reusable frameworks, engagement notes |
| `researcher` | planned | Methodology decisions, literature notes, experiments |
| `investor` | planned | Investment memos, theses, diligence, deal notes |
| `devops` | planned | Infra decisions, postmortems, runbooks, on-call logs |
| `data` | planned | Experiment decisions, model and dataset rationale, reproducibility |
| `security` | planned | Threat models, vuln triage, controls, audit notes |
| `teacher` | planned | Curriculum decisions, lesson patterns, assessments |
| `sales` | planned | Deal decisions, playbooks, account notes, pipeline |
| `recruiter` | planned | Candidate decisions, sourcing, scorecards, pipeline |
| `architect` | planned | Building design decisions, code compliance, detailing, projects |

## License

[Apache 2.0](./LICENSE).
