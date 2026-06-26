# todo.md — RawLog Triage Pipeline

Full phase checklist. Plan-first, verify-before-done, ruff-clean, push-every-phase.
Check items off as they complete; add a review section at the end of each phase.

> Per-pair task detail and sequencing live in [docs/GROUP_A_Om_Pranav.md](../docs/GROUP_A_Om_Pranav.md)
> and [docs/GROUP_B_Venkatesh_Vamsi.md](../docs/GROUP_B_Venkatesh_Vamsi.md). The integration
> contract (signatures, `interfaces.py`, severity values) is in [docs/TRD.md](../docs/TRD.md).

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

## Phase 1 — Schema & contract
- [x] Define `TriageResult` Pydantic v2 model (4 fields exactly) in `schema.py` — **Group A publishes FIRST**
- [x] Severity values `INFO`/`WARNING`/`ERROR`/`FATAL`; add `Field(description=...)` to every field
- [x] Agree `ingest()`/`triage()`/`emit()` signatures in `interfaces.py` (per docs/TRD.md)
- [x] Export JSON schema for Ollama (`TriageResult.model_json_schema()`) — 4 props, `additionalProperties: false`
- [x] Unit tests: valid payload passes, extra/missing field fails, bad enum fails (5 tests)
- [ ] **Tooling migration (Group B):** `uv` env/deps + `pre-commit` framework + CI — replaces Phase-0 pip/venv + native hook
- [x] ruff clean · pytest green · commit + push

## Phase 2 — Ingestion + pre-filter (Group B)
- [ ] `ingest(path) -> list[str]`: read with `errors="replace"`, chunk, pre-filter benign INFO/DEBUG (stdlib `re`)
- [ ] Handle empty input / missing file with clear errors; keep memory flat on large files
- [ ] Add a ~500KB Loghub sample → `data/sample_production_logs.txt`
- [ ] Unit tests with the sample + stdin
- [ ] ruff clean · pytest green · commit + push

## Phase 3 — Triage (Group A)
- [x] `ollama pull gemma3:4b` (prerequisite) — pulled & smoke-tested
- [x] `triage(chunk, model="gemma3:4b") -> TriageResult | None` via `ollama` client (`format=TriageResult.model_json_schema()`, `options={"temperature": 0}`)
- [x] Return `None` when there is no real error (severity INFO → None; no fabrication); bounded 1-retry on `ValidationError`, then a typed "unparseable" result
- [x] System prompt that isolates the single most severe anomalous/fatal event
- [x] Tests (mock Ollama client) for parse / validate / None / unparseable paths (4 tests)
- [x] Live self-check (`python -m rawlog_triage.triage`) returns a valid FATAL TriageResult on the sample
- [x] ruff clean · pytest green · commit + push

## Phase 4 — Orchestration + emit (Group B)
- [ ] `emit(result, target="-")`: `"-"` → stdout; a path → write file; `http(s)://…` → POST
- [ ] `cli.py` wires ingest → triage → emit, arg parsing, exit codes
- [ ] End-to-end run on `data/sample_production_logs.txt`
- [ ] ruff clean · pytest green · commit + push

## Phase 5 — Hardening (Group B)
- [ ] Validation-failure path: non-zero exit, clear stderr, never malformed stdout JSON
- [ ] Edge cases: empty file · no-error file (→ `None`, no fabrication) · truncated/garbled lines · multiple fatals (report the FIRST) · non-UTF-8 bytes · huge file
- [ ] Ollama-unavailable / model-missing handling
- [ ] Run on an unseen organizer sample; fix whatever breaks
- [ ] ruff clean · pytest green · commit + push

## Phase 6 — Eval (Group A)
- [ ] `eval/golden.jsonl`: 10–20 hand-labelled Loghub lines (expected severity + key fields)
- [ ] `eval/run_eval.py` reports JSON-valid %, correct-line %, severity accuracy (the demo slide)
- [ ] Compare `gemma3:4b` vs `gemma3:12b` on the golden set (if time allows)
- [ ] Record results · ruff clean · pytest green · commit + push

## Phase 7 — Demo
- [ ] Demo script / README usage walkthrough (one command, end-to-end)
- [ ] Sample webhook POST example
- [ ] Lock a submittable version ~2 hrs before close; then polish metrics + demo
- [ ] Final pass: ruff clean · pytest green · commit + push

---

## Phase 0 — Review

**Built (scaffolding + governance only — no pipeline/feature code):**
- Repo structure: `src/rawlog_triage/{__init__,schema,ingest,triage,emit,cli}.py` (stubs —
  module docstrings + `# TODO(phase-…)`; `cli.main()` is a placeholder), plus
  `tests/`, `data/` (with `sample.log`), `eval/`, `tasks/`, `docs/`, `scripts/`.
- Governance: `CLAUDE.md` (rules + workflow), `docs/PRD.md` (exact 4-field contract),
  `docs/TRD.md` (stack + ingest→triage→emit contract), `tasks/todo.md` (this checklist),
  `docs/lessons.md`, `docs/instructions.md`, plus a short `README.md`.
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

**Post-Phase-0 docs update (team governance):**
- Promoted the team operating manual to root `CLAUDE.md` (Group A/B ownership, agent-tool
  usage, guards); removed the duplicate `docs/CLAUDE.md` so it auto-loads.
- Added `docs/GROUP_A_Om_Pranav.md` and `docs/GROUP_B_Venkatesh_Vamsi.md`; expanded PRD/TRD/lessons.
- Tooling target moved to `uv` + `pre-commit` framework + CI + branch-per-phase, but the
  working pip/venv + native-hook scaffold is kept; **migration tracked as a Phase-1 Group-B task** above.

**Deferred / next:**
- **Before Phase 3 (triage): `ollama pull gemma3:4b`** — not yet pulled locally
  (only `gemma2:2b`, `qwen2.5:14b`, `llama3.2:3b`, `nomic-embed-text` are present).
- Phase 1 = publish `schema.py` (`TriageResult`) + agree `interfaces.py` signatures.
