# CLAUDE.md — RawLog Triage Pipeline
GDG Cloud Boston × Northeastern · Gemma Hackathon · Jun 26, 2026

Operating manual for every AI coding session (Claude Code Opus + GitHub Copilot CLI) on this repo. **Read this at the start of every phase chat.**

---

## What we're building
A Python CLI that ingests a raw server/system log dump, uses a **local Gemma model (via Ollama)** to find the single anomalous/fatal event, and emits **one schema-validated JSON object** (`service_name`, `timestamp`, `error_severity`, `suggested_remediation`) ready for a webhook. See `docs/PRD.md` (requirements) and `docs/TRD.md` (design + the integration contract).

**This is an INFERENCE + prompt-engineering project, not model training.** Do NOT fine-tune, tune hyperparameters, add early stopping, or write a CUDA training loop — none apply here. The GPU is only used for fast inference.

## Team & ownership (two pairs, two machines, one repo)
- **Group A — Intelligence Core (Om + Pranav):** owns `src/rawlog_triage/schema.py` + `triage.py`, the system prompt, the structured-output call, validate/repair, and `eval/`.
- **Group B — Pipeline & Hardening (Venkatesh + Vamsi):** owns `ingest.py`, `emit.py`, `cli.py`, the edge-case test harness, and repo hygiene/CI.

Both groups code to the contract in `docs/TRD.md`. `schema.py` is published by Group A first; Group B stubs `triage()` until it lands. See `docs/GROUP_A_Om_Pranav.md` / `docs/GROUP_B_Venkatesh_Vamsi.md`.

---

## Installed agent tools — USE THEM

### ponytail — build discipline (level: full)
Think like the laziest senior dev. The best code is the code never written. Before writing anything, climb the ladder: **does this need to exist (YAGNI)? → reuse what's already in the repo → stdlib → native platform feature → an already-installed dependency → one line → the minimum that works.**

NOT lazy about (these are what win this hackathon): understanding the problem first, **input validation at trust boundaries, error handling that prevents data loss, security**, and the ONE runnable check every non-trivial function leaves behind. Mark deliberate shortcuts with a `# ponytail:` comment naming the ceiling + upgrade path.

Switch with `/ponytail lite|full|ultra`. **Keep `full`.** The eval harness and golden-set tests are explicitly-required deliverables, so do not let `ultra` trim them away.

### graphify — token saver across phase chats (run after every phase)
We use a new chat per phase to save tokens; graphify makes that cheap by turning the repo into a queryable knowledge graph so the agent navigates structure instead of re-reading every file.
- **START of each phase chat:** read `graphify-out/GRAPH_REPORT.md` before exploring files.
- **END of each phase (after merge):** run `/graphify` (PowerShell: `graphify .`) to refresh the graph.
- `graphify-out/` is gitignored — each machine regenerates locally (the artifacts embed file contents and are large).

> Note: graphify and ponytail may append their own sections to `CLAUDE.md` / `AGENTS.md` when installed — that's expected. Keep the project content above their auto-added sections.

---

## Workflow (every phase)
1. **PLAN FIRST.** Enter plan mode for any task with 3+ steps or an architectural choice. Show the plan; wait for approval. If something goes sideways, STOP and re-plan — don't push through.
2. **TRACK** in `tasks/todo.md` with checkboxes; mark items done as you go. Use your group's guide for the task list.
3. **VERIFY before "done".** Prove it works: run it, run the check, show the output. Ask: "Would a staff engineer approve this?" Never mark complete on faith.
4. **EXPLAIN** changes at a high level at each step.
5. **CAPTURE LESSONS.** After ANY correction from a teammate or a mistake you made: append it to `docs/lessons.md` (what went wrong + the rule) AND add a one-line guard to the "Guards" section below so it never repeats.
6. **PUSH every phase.** Branch per phase (`git checkout -b phaseN-<group>`), run `ruff check . && ruff format --check . && pytest -q`, then push. CI runs ruff + pytest on every push/PR.

## Stack guards (detail in docs/TRD.md)
- Python 3.12, `uv` for env/deps. Pydantic v2.
- Model call: `ollama` Python client, `format=TriageResult.model_json_schema()`, `options={"temperature": 0}`. Constrained decoding makes invalid JSON impossible — **do NOT hand-roll regex JSON repair as the primary path.**
- Default model `gemma3:4b` (fast iteration). `gemma3:12b` only if accuracy is short and VRAM allows.
- Minimal deps. No LangChain. No database. Emit JSON to file/stdout (optional webhook POST).

> Phase 0 status: the committed scaffold currently uses pip/venv + a native git hook (`core.hooksPath`) and commits to `main`. Migrating to `uv` + the `pre-commit` framework + CI + branch-per-phase is a Phase-1 Group-B task (tracked in `tasks/todo.md`).

## Guards (append a line here after every mistake)
- Classify the task first: inference vs training. This is **inference** — the GPU only speeds inference.
- Prefer Ollama structured outputs over prompt-only "return JSON"; the latter is unreliable and slower.
- Scope to the actual track (log triage); don't build features the rubric doesn't ask for.
- _<add new guards here as mistakes happen>_
