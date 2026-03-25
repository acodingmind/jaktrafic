# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Speckit**-based project (v0.4.1) using spec-driven development. It uses GitHub Copilot as its AI backend (`init-options.json: "ai": "copilot"`). The repository currently contains only the Speckit scaffolding — no application source code has been written yet.

The project uses **sequential branch numbering** (e.g., `001-feature-name`, `002-feature-name`) for feature branches. Feature specs live under `specs/<branch-name>/`.

## Speckit Workflow

The development workflow follows a strict pipeline of agent commands, each building on the previous:

1. **`/speckit.constitution`** — Define or update project principles in `.specify/memory/constitution.md`
2. **`/speckit.specify`** — Create a feature spec from a natural language description. Creates a numbered feature branch and `specs/<branch>/spec.md`
3. **`/speckit.clarify`** — Ask up to 5 targeted clarification questions to reduce ambiguity in the spec (must run before planning)
4. **`/speckit.plan`** — Generate `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` inside the feature's spec directory
5. **`/speckit.checklist`** — Generate requirements-quality checklists (unit tests for English, not implementation tests)
6. **`/speckit.tasks`** — Generate `tasks.md` organized by user story with phased execution (Setup → Foundational → User Stories by priority → Polish)
7. **`/speckit.analyze`** — Read-only consistency analysis across spec/plan/tasks (never modifies files)
8. **`/speckit.implement`** — Execute the task plan phase-by-phase, respecting dependencies and TDD ordering
9. **`/speckit.taskstoissues`** — Convert tasks into GitHub issues (requires GitHub remote)

Each command depends on outputs from earlier steps. Do not skip steps unless explicitly told.

## Key Scripts

All scripts are in `.specify/scripts/bash/` and must be run from the repo root:

- **`check-prerequisites.sh --json`** — Validates feature branch, returns `FEATURE_DIR` and `AVAILABLE_DOCS` as JSON. Supports `--require-tasks`, `--include-tasks`, `--paths-only` flags.
- **`create-new-feature.sh "<description>" --json --short-name "<name>"`** — Creates a numbered branch and initializes `specs/<branch>/spec.md` from template. Never pass `--number` (auto-detected). Run only once per feature.
- **`setup-plan.sh --json`** — Copies plan template into the feature directory.
- **`update-agent-context.sh [agent_type]`** — Updates agent context files (CLAUDE.md, AGENTS.md, etc.) from plan.md data. Called during the plan phase.
- **`common.sh`** — Shared functions: `get_repo_root`, `get_current_branch`, `has_git`, `find_feature_dir_by_prefix`, `resolve_template`, `json_escape`. Sources itself via `BASH_SOURCE`.

The `get_repo_root` function prioritizes `.specify/` directory over `.git` to locate the project root. `resolve_template` uses a priority stack: overrides → presets → extensions → core templates.

## Directory Layout

- `.specify/memory/constitution.md` — Project constitution (principles, governance). Currently a template with placeholders — must be filled via `/speckit.constitution` before meaningful work.
- `.specify/templates/` — Templates for spec, plan, tasks, checklists, and agent files. Templates use `[PLACEHOLDER]` tokens.
- `.github/agents/` — Speckit agent definitions (GitHub Copilot prompt files)
- `.github/prompts/` — Speckit prompt files
- `specs/` — Created per-feature as `specs/<branch-name>/` containing spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/, quickstart.md, and checklists/

## Important Conventions

- Feature branches follow the pattern `NNN-short-name` (sequential) or `YYYYMMDD-HHMMSS-short-name` (timestamp). Scripts validate this via regex.
- The `SPECIFY_FEATURE` env var can override git branch detection for non-git workflows.
- Spec files must focus on **WHAT** and **WHY**, never implementation details. Specs are written for business stakeholders.
- Checklists validate **requirements quality** (completeness, clarity, consistency), not implementation behavior. Items must never start with "Verify", "Test", or "Confirm" + implementation behavior.
- Task IDs follow `T001`, `T002` format. `[P]` marks parallelizable tasks. `[US1]`, `[US2]` labels map tasks to user stories.
- Tasks are phased: Setup → Foundational (blocking) → User Story phases by priority → Polish.
- The constitution (`.specify/memory/constitution.md`) is authoritative — constitution violations are always CRITICAL in analysis.
- Use `--json` flag on all scripts when parsing output programmatically; scripts support both `jq` and fallback manual JSON construction.
- For shell arguments containing single quotes, use escape syntax: `'I'\''m Groot'` or double-quote when possible.
- Always use absolute paths when working with Speckit scripts.
- Use a Python venv for any Python dependencies.
