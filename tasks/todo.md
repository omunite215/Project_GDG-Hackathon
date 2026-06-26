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
- [x] **Tooling migration (Group B):** `uv` env/deps + `pre-commit` framework + CI — replaces Phase-0 pip/venv + native hook
- [x] ruff clean · pytest green · commit + push

## Phase 2 — Ingestion + pre-filter (Group B)
- [x] `ingest(path) -> list[str]`: read with `errors="replace"`, chunk, pre-filter benign INFO/DEBUG (stdlib `re`)
- [x] Handle empty input / missing file with clear errors; keep memory flat on large files
- [x] Add a ~500KB Loghub sample → `data/sample_production_logs.txt`
- [x] Unit tests with the sample + stdin
- [x] ruff clean · pytest green · commit + push

## Phase 3 — Triage (Group A)
- [x] `ollama pull gemma3:4b` (prerequisite) — pulled & smoke-tested
- [x] `triage(chunk, model="gemma3:4b") -> TriageResult | None` via `ollama` client (`format=TriageResult.model_json_schema()`, `options={"temperature": 0}`)
- [x] Return `None` when there is no real error (severity INFO → None; no fabrication); bounded 1-retry on `ValidationError`, then a typed "unparseable" result
- [x] System prompt that isolates the single most severe anomalous/fatal event
- [x] Tests (mock Ollama client) for parse / validate / None / unparseable paths (4 tests)
- [x] Live self-check (`python -m rawlog_triage.triage`) returns a valid FATAL TriageResult on the sample
- [x] ruff clean · pytest green · commit + push

## Phase 4 — Orchestration + emit (Group B)
- [x] `emit(result, target="-")`: `"-"` → stdout; a path → write file; `http(s)://…` → POST
- [x] `cli.py` wires ingest → triage → emit, arg parsing, exit codes (`--model` threaded to `triage()`)
- [x] End-to-end run on `data/sample_production_logs.txt`
- [x] ruff clean · pytest green · commit + push

## Phase 5 — Hardening (Group B)
- [x] Validation-failure path: non-zero exit, clear stderr, never malformed stdout JSON
- [x] Edge cases: empty file · no-error file (→ `None`, no fabrication) · truncated/garbled lines · multiple fatals (report the FIRST) · non-UTF-8 bytes · huge file
- [x] Ollama-unavailable / model-missing handling
- [x] Run on an unseen organizer sample; fix whatever breaks
- [x] ruff clean · pytest green · commit + push

## Phase 6 — Eval (Group A)
- [x] `eval/golden.jsonl`: 10 hand-labelled cases (INFO→FATAL + 2 no-incident + buried-fatal). Starter set — expand with real Loghub lines.
- [x] `eval/run_eval.py` reports JSON-valid %, detection %, severity accuracy (the demo slide)
- [ ] Compare `gemma3:4b` vs `gemma3:12b` on the golden set — pending `ollama pull gemma3:12b` (~8 GB); `--model` flag ready
- [x] Record results (`gemma3:4b`): **JSON-valid 10/10 (100%) · detection 10/10 (100%) · severity 7/8 (88%)** · ruff clean · pytest 21 green · commit + push

> Eval data note: the golden set is realistic-but-synthetic. Group B's `data/sample_production_logs.txt`
> (real Loghub ~500KB) still needs committing to expand the set and run end-to-end on real data.

## Phase 7 — Demo
- [ ] Demo script / README usage walkthrough (one command, end-to-end)
- [ ] Sample webhook POST example
- [ ] Lock a submittable version ~2 hrs before close; then polish metrics + demo
- [ ] Final pass: ruff clean · pytest green · commit + push

---

## Phase 5 — Review (Group B hardening)

Integrated on top of Group A's Phase 3 (real `triage()`). `triage.py`/`interfaces.py`
are Group A's; this branch owns `ingest.py`, `emit.py`, `cli.py`, and the pipeline tests.

**Done + tested** (`tests/test_pipeline.py`, 11 tests; full suite green, Ollama never hit):
- Edge cases: empty file · benign no-incident emits nothing (triage→None path) · truncated/garbled lines kept as candidates · non-UTF-8 bytes (`errors="replace"`) · large file flushes into bounded chunks (memory stays flat).
- CLI failure paths: unreadable input → clear stderr + exit 2; any `triage()` failure (Ollama unreachable / model missing) → clear stderr + exit 1; stdout never carries a partial/malformed payload. CLI tests mock `triage` so they stay hermetic.
- `--model` is threaded from the CLI into `triage(chunk, model=...)`.
- Fixed a latent bug: the chunk buffer only flushed on anomaly-keyword lines, so a long run of non-anomaly candidates grew unbounded — now flushes on size regardless of line shape.

**Known limitation (coordinate with Group A):**
- "Report the FIRST fatal": `ingest()` preserves order and the CLI triages `chunks[0]`, so the earliest fatal within the first ~2000-char chunk is reported. A fatal that lands in a later chunk would need the CLI to triage subsequent chunks — deferred (extra model calls).
- Recall-first pre-filter keeps benign non-INFO/DEBUG lines; the no-fabrication guarantee rests on Group A's `triage()` mapping benign chunks to severity INFO → `None` (implemented in Phase 3).

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
