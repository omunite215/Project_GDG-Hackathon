# CLAUDE.md — RawLog Triage Pipeline

Project rules and workflow. These are binding for every phase.

## What this project is
A Python utility that reads raw server/system logs, uses a local Gemma model via
Ollama to isolate the single anomalous/fatal line, and emits a schema-validated
JSON object ready for a webhook. See [docs/PRD.md](docs/PRD.md) and
[docs/TRD.md](docs/TRD.md).

## The output contract is sacred
Every successful run emits **exactly** these 4 fields — no more, no fewer:
`service_name`, `timestamp`, `error_severity`, `suggested_remediation`.
The Pydantic model in `schema.py` is the single source of truth and is the JSON
schema passed to Ollama via `format=`. Do not add fields without updating PRD + TRD.

## Workflow (follow every phase)
1. **Plan first.** Enter plan mode and get approval before writing code for a phase.
   No feature code lands without an approved plan.
2. **Verify before marking done.** "Done" means: `ruff check .` clean,
   `ruff format --check .` clean, `pytest` green, AND the code was actually exercised
   (run it on real input). Report failures honestly with output — never claim success
   you didn't observe.
3. **Record every mistake.** When something breaks (a bug, a wrong assumption, a failed
   command), append the mistake **and its fix** to [docs/lessons.md](docs/lessons.md)
   so it never repeats. Check lessons.md before starting work.
4. **ruff must be clean before every commit.** Enforced by the pre-commit hook
   (`scripts/hooks/pre-commit` via `core.hooksPath`). Never bypass with `--no-verify`.
5. **Push every phase to GitHub** (`origin`, branch `main`) once it is verified.
6. **Keep [tasks/todo.md](tasks/todo.md) current.** Check off completed items; add a
   short review section at the end of each phase.

## Engineering principles
- **Simplicity first.** The laziest correct solution wins. No speculative abstractions,
  no flexibility nobody asked for.
- **Minimal dependencies.** Reach for the standard library before adding a package.
  Current runtime deps are only `pydantic` and `ollama`.
- **Senior-engineer standards.** Clear names, small functions, type hints, docstrings on
  public functions. Match the style of surrounding code.
- **Determinism.** All Ollama calls use `temperature=0` and structured outputs
  (`format=<schema>`). The pipeline must be reproducible.

## Stack (see TRD for detail)
Python ≥3.12 · Ollama + `gemma3:4b` (dev) / `gemma3:12b` (quality) · Pydantic v2 ·
ruff · pytest. Run `ollama pull gemma3:4b` before the triage phase.
