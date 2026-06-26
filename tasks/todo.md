# todo.md — RawLog Triage Pipeline

Full phase checklist. Plan-first, verify-before-done, ruff-clean, push-every-phase.
Check items off as they complete; add a review section at the end of each phase.

## Phase 0 — Scaffolding & governance
- [x] Repo structure (`src/rawlog_triage/`, `tests/`, `data/`, `eval/`, `tasks/`, `docs/`, `scripts/`)
- [x] Source stubs: `__init__`, `schema`, `ingest`, `triage`, `emit`, `cli`
- [x] Governance docs: `CLAUDE.md`, `docs/PRD.md`, `docs/TRD.md`, `docs/lessons.md`, `docs/instructions.md`, `tasks/todo.md`
- [x] `pyproject.toml` (deps + ruff + pytest)
- [x] `Makefile` + `scripts/*.ps1`
- [x] Pre-commit hook (`scripts/hooks/pre-commit` via `core.hooksPath`)
- [x] `.gitignore`
- [x] Smoke test green; `ruff check .` + `ruff format --check .` clean
- [x] Commit + push to `origin/main`

## Phase 1 — Schema
- [ ] Define `TriageResult` Pydantic v2 model (4 fields exactly)
- [ ] Define `error_severity` enum (CRITICAL/FATAL/ERROR/WARNING/INFO)
- [ ] Export JSON schema for Ollama `format=`
- [ ] Unit tests: valid payload passes, extra/missing field fails, bad enum fails
- [ ] ruff clean · pytest green · commit + push

## Phase 2 — Ingestion
- [ ] `ingest.read(source)` — file path or stdin → normalized log text
- [ ] Handle empty input / missing file with clear errors
- [ ] Unit tests with `data/sample.log` + stdin
- [ ] ruff clean · pytest green · commit + push

## Phase 3 — Triage
- [ ] `ollama pull gemma3:4b` (prerequisite)
- [ ] `triage.run(log_text, model)` → Ollama call, `temperature=0`, `format=schema`
- [ ] Parse + validate response into `TriageResult`
- [ ] Prompt that instructs isolation of the single fatal/anomalous line
- [ ] Tests (mock Ollama client) for parse/validate paths
- [ ] ruff clean · pytest green · commit + push

## Phase 4 — Orchestration
- [ ] `emit.to_json(result)` → exact 4-field JSON string
- [ ] `cli.main()` wires ingest → triage → emit, arg parsing, exit codes
- [ ] End-to-end run on `data/sample.log`
- [ ] ruff clean · pytest green · commit + push

## Phase 5 — Hardening
- [ ] Validation-failure path: non-zero exit, clear stderr, never malformed stdout JSON
- [ ] Ollama-unavailable / model-missing handling
- [ ] Timeouts / large-input handling
- [ ] Tests for failure modes
- [ ] ruff clean · pytest green · commit + push

## Phase 6 — Eval
- [ ] Curate `eval/` cases (raw log → expected isolated line + fields)
- [ ] Eval harness measuring isolation correctness + validity rate
- [ ] Compare `gemma3:4b` vs `gemma3:12b`
- [ ] Record results · ruff clean · pytest green · commit + push

## Phase 7 — Demo
- [ ] Demo script / README usage walkthrough
- [ ] Sample webhook POST example
- [ ] Final pass: ruff clean · pytest green · commit + push

---

## Phase 0 — Review

**Built (scaffolding + governance only — no pipeline/feature code):**
- Repo structure: `src/rawlog_triage/{__init__,schema,ingest,triage,emit,cli}.py` (stubs —
  module docstrings + `# TODO(phase-…)`; `cli.main()` is a placeholder), plus
  `tests/`, `data/` (with `sample.log`), `eval/`, `tasks/`, `docs/`, `scripts/`.
- Governance: `CLAUDE.md` (rules + workflow), `docs/PRD.md` (exact 4-field contract),
  `docs/TRD.md` (stack + ingest→triage→emit contract), `tasks/todo.md` (this checklist),
  `docs/lessons.md` (empty), `docs/instructions.md`, plus a short `README.md`.
- Tooling: `pyproject.toml` (deps `pydantic`,`ollama`; dev `ruff`,`pytest`; ruff + pytest
  config; hatchling src layout; `rawlog-triage` console script), `Makefile`,
  `scripts/*.ps1`, and a native pre-commit hook (`scripts/hooks/pre-commit` via
  `core.hooksPath`). `.gitignore` added.

**Verified:**
- `.venv` created; `pip install -e .[dev]` succeeded.
- `ruff check .` → All checks passed.
- `ruff format --check .` → clean (8 files).
- `pytest` → 1 passed (smoke test), exit 0.
- `import rawlog_triage` → OK (v0.0.0); console script prints the placeholder.
- Committed to `main` and pushed to existing `origin`.

**Decisions / deviations:**
- GitHub repo already existed (`omunite215/Project_GDG-Hackathon`) → pushed to it rather
  than creating a new one. `gh` CLI not installed (not needed).
- `requires-python = ">=3.12"`; dev machine runs Python 3.13.7 (compatible).
- `.claude/` gitignored (session-generated agent config, not a deliverable).

**Deferred / next:**
- **Before Phase 3 (triage): `ollama pull gemma3:4b`** — not yet pulled locally
  (only `gemma2:2b`, `qwen2.5:14b`, `llama3.2:3b`, `nomic-embed-text` are present).
- Phase 1 = define the `TriageResult` Pydantic model + `error_severity` enum.
