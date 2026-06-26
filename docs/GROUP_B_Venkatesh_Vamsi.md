# GROUP B — Pipeline & Hardening (Venkatesh + Vamsi)

You own everything around the model: getting data in, wiring the pipeline, getting JSON out, and trying to break it.

## Your files
```
src/rawlog_triage/ingest.py
src/rawlog_triage/emit.py
src/rawlog_triage/cli.py
tests/                          # edge-case harness — Vamsi leads adversarial inputs
pyproject.toml / ruff / pre-commit / CI    # repo hygiene
```

## One-time setup (your machine)
```bash
winget install astral-sh.uv
git clone <repo-url> && cd rawlog-triage
uv sync --all-extras

# You also need Ollama to run the pipeline end-to-end:
winget install Ollama.Ollama
ollama pull gemma3:4b
# If only Group A's machine has the strong GPU, point at it instead of pulling locally:
#   Windows:  set OLLAMA_HOST=http://<groupA-machine-ip>:11434
#   Mac/Linux: export OLLAMA_HOST=http://<groupA-machine-ip>:11434

# Data — from the Loghub repo, save a ~500KB HDFS or Linux sample as:
#   data/sample_production_logs.txt

# Agent tools (same on both machines)
uv tool install graphifyy && graphify install --project
# ponytail (Claude Code):  /plugin marketplace add DietrichGebert/ponytail ; /plugin install ponytail@ponytail
# ponytail (Copilot CLI):  copilot plugin marketplace add DietrichGebert/ponytail ; copilot plugin install ponytail@ponytail
```

## Your todo (mirror into tasks/todo.md)
**Phase 1 — Contract (with Group A, ~20 min)**
- [ ] Confirm `ingest()`/`triage()`/`emit()` signatures in `interfaces.py`.
- [ ] Add a **stub `triage()`** returning a fixed `TriageResult` so you can build before Group A's lands.

**Phase 2 — Ingestion + pre-filter (your core)**
- [ ] `ingest(path) -> list[str]`: read the file with `errors="replace"`, split into chunks, drop obviously-benign INFO/DEBUG lines with cheap regex so the model only sees candidate anomalies. `# ponytail: stdlib re, no parser lib`.
- [ ] Keep memory flat on large files (iterate, don't slurp-and-hold).

**Phase 4 — Orchestration + emit**
- [ ] `emit(result, target="-")`: `"-"` → stdout; a path → write file; `http(s)://…` → POST (`requests`). One small function.
- [ ] `cli.py` (typer): `triage-logs <input> [--target ...] [--model gemma3:4b]`. Wire ingest → triage → emit.

**Phase 5 — Hardening (your differentiator + Vamsi's wheelhouse)**
- [ ] `tests/` for: empty file; no-error file (→ `None`, assert no fabrication); truncated/garbled lines; multiple fatals (assert FIRST is reported); non-UTF-8 bytes; large file.
- [ ] Run on an unseen organizer sample; fix whatever breaks. `ruff` + `pytest` green before each push.

## Your first prompt (Phase 2 chat)
```
Read CLAUDE.md, TRD.md, and graphify-out/GRAPH_REPORT.md first. ponytail full.

Implement src/rawlog_triage/ingest.py against the contract in TRD.md.
ingest(path: str) -> list[str] reads a raw log file (open with errors="replace"),
splits it into chunks, and pre-filters obviously-benign INFO/DEBUG lines with cheap
stdlib regex so downstream only sees candidate anomaly/fatal lines. Keep memory flat
on large files. No parser dependency — re is enough.

Plan first, show the plan, wait for approval. Leave ONE assert-based self-check on a
small fixture (a few benign lines + one ERROR line) proving the benign lines are
dropped and the ERROR line survives. Run it and show output. Keep it minimal.
```

## Integration notes
- Use a **stub `triage()`** (fixed `TriageResult`) until Group A pushes the real one — you can build and test the whole pipeline without the model.
- **Own the green build:** `pyproject` + `ruff` + `pre-commit` + CI so every push from both groups stays clean.
