# GROUP A — Intelligence Core (Om + Pranav)

You own the brain: getting Gemma to turn a candidate log chunk into a valid `TriageResult`, and proving it works.

## Your files
```
src/rawlog_triage/schema.py     # publish FIRST — Group B depends on it
src/rawlog_triage/triage.py
eval/run_eval.py
eval/golden.jsonl
```

## One-time setup (your machine)
```bash
# Python + deps
winget install astral-sh.uv            # Mac/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repo-url> && cd rawlog-triage
uv sync --all-extras                   # after Phase 0 creates pyproject; before that:
                                       # uv add ollama pydantic typer && uv add --dev pytest ruff pre-commit

# Ollama + model
winget install Ollama.Ollama
ollama pull gemma3:4b
ollama run gemma3:4b "reply with one word: ready"   # smoke test

# Agent tools (same on both machines)
uv tool install graphifyy              # CLI is `graphify`
graphify install --project             # registers the skill; run `graphify install --help` for per-platform flags (e.g. --platform codex)
# Claude Code:    /plugin marketplace add DietrichGebert/ponytail
#                 /plugin install ponytail@ponytail
# Copilot CLI:    copilot plugin marketplace add DietrichGebert/ponytail
#                 copilot plugin install ponytail@ponytail
```

## Your todo (mirror into tasks/todo.md)
**Phase 1 — Contract (with Group B, ~20 min)**
- [ ] Write `schema.py` (`TriageResult` per TRD). **Commit + push immediately** so Group B can build.
- [ ] Agree the `ingest()` / `triage()` / `emit()` signatures in `interfaces.py`.

**Phase 3 — Triage call (your core)**
- [ ] `triage(chunk)` via `ollama.chat(model, messages, format=TriageResult.model_json_schema(), options={"temperature": 0})`.
- [ ] System prompt (tight): *"You are a log triage engine. Given a log excerpt, identify the single most severe anomalous/fatal event and fill the schema. If there is no error, return nothing."*
- [ ] Return `None` when the chunk has no real error — **do not fabricate**. Leave one assert-based self-check.
- [ ] Bounded fallback: on `ValidationError`, retry once, then return a typed "unparseable" result. `# ponytail: 1 retry only`.

**Phase 5 — Eval (your differentiator)**
- [ ] Build `eval/golden.jsonl`: 10–20 real Loghub lines, hand-labelled (expected severity + key fields).
- [ ] `eval/run_eval.py` prints **JSON-valid %, correct-line %, severity accuracy** — this is the demo slide.
- [ ] If time: compare `gemma3:4b` vs `gemma3:12b` on the golden set; keep whichever wins within the latency budget.

## Your first prompt (Phase 3 chat)
```
Read CLAUDE.md, TRD.md, and graphify-out/GRAPH_REPORT.md first. ponytail full.

Implement src/rawlog_triage/triage.py against the contract in TRD.md.
triage(chunk: str) -> TriageResult | None must call the local Ollama Gemma model
using the ollama Python client with format=TriageResult.model_json_schema() and
options={"temperature": 0} (constrained decoding — do NOT add regex JSON repair as
the primary path). Return None when the chunk contains no real error; never fabricate
one. On pydantic ValidationError, retry once, then return a typed unparseable result.

Plan first, show me the plan, wait for approval. Leave ONE assert-based self-check
that fails if triage() returns invalid output on a known-bad sample line. Run it and
show the output. Keep it minimal.
```

## Integration notes
- **Publish `schema.py` before anything else**; ping Group B the moment it's pushed.
- You don't need real `ingest()`/`emit()` to develop — feed `triage()` a hard-coded bad line.
- When Group B's pipeline lands, run the full CLI on the sample together.
