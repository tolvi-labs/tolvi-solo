# tolvi-solo

A vault for solo builders. Capture decisions, patterns, and session notes as plain Markdown - searchable, committable, and readable by AI agents without any server setup.

> **Status:** Early. Engineer pack is the first vertical. Writer, CPA, and Entrepreneur packs are planned.

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
- **`tolvi-sync` (PreToolUse, git commit)** - fires before every commit; auto-stages vault changes and blocks the commit if no session note exists for today, so the vault is always committed alongside the code

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

## Packs

| Pack | Status | Verticals |
|---|---|---|
| `engineer` | ✅ | Tech choices, architecture, dependencies, process |
| `writer` | planned | Projects, drafts, editorial decisions, source tracking |
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
