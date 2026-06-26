# TRD.md — RawLog Triage Pipeline

## Stack (verified current, Jun 2026)
- **Python 3.12**, managed with **uv**.
- **Ollama** (v0.30.x) serving Gemma locally. The GPU is used automatically for inference.
- **Models:** `gemma3:4b` = dev default (instant on this hardware, ideal for prompt iteration). `gemma3:12b` = optional quality upgrade (~8–9 GB at Q4; if the GPU is the 8 GB laptop part it spills to the 64 GB system RAM and runs slower — only switch if 4B accuracy is short and the latency budget allows). **Stay in the Gemma family — this is a Gemma-powered event.**
- **Pydantic v2** for schema + validation.
- **typer** (or stdlib `argparse`) for the CLI. `requests` only if doing the optional webhook POST.
- Dev: **pytest**, **ruff** (check + format), **pre-commit**.
- No LangChain, no DB. (ponytail: add a dependency only when a few lines can't do the job.)

## The key technique: Ollama structured outputs
Pass the Pydantic JSON schema to Ollama's `format` parameter with **temperature 0**. Ollama applies **constrained decoding**, so the model literally cannot emit a token that breaks the schema — no code fences, no conversational filler, no invalid JSON — and it's markedly faster than free-form generation. This is how we hit "100% valid JSON" with no regex-repair stage. A bounded validate-and-retry (max 1–2 tries, then return a typed "unparseable" record) is the only fallback we need.

Best practices: `temperature=0`; add `Field(description=...)` to every field (the description ships in the schema and measurably improves extraction); keep the schema **flat** (ours is — 4 fields, no nesting, which also avoids the one failure mode where small quantized models return empty arrays on deeply nested schemas).

## Architecture (linear pipeline)
```
ingest(path) -> list[str]              # Group B: read file, chunk, pre-filter benign noise
   -> triage(chunk) -> TriageResult?   # Group A: Gemma structured-output call
       -> emit(result) -> None         # Group B: JSON to stdout/file (optional webhook POST)
```
Orchestrated by `cli.py` (Group B).

**Pre-filter rationale (Group B):** drop obviously-benign INFO/DEBUG lines with cheap regex BEFORE the model, so tokens are spent only on candidate anomaly lines. This is the bandwidth win on a 500KB dump.

## The integration contract
Both groups code to this. **Do not change it without telling the other pair.**

```python
# src/rawlog_triage/schema.py   (owned by Group A — publish FIRST)
from pydantic import BaseModel, Field
from typing import Literal

Severity = Literal["INFO", "WARNING", "ERROR", "FATAL"]

class TriageResult(BaseModel):
    service_name: str = Field(description="Service/component that emitted the failing line")
    timestamp: str = Field(description="ISO-8601 timestamp of the event, or '' if none present")
    error_severity: Severity
    suggested_remediation: str = Field(description="One concrete next step to investigate/fix")
```

```python
# src/rawlog_triage/interfaces.py   (signatures only — the seam between the two pairs)
# ingest(path: str) -> list[str]
# triage(chunk: str) -> TriageResult | None      # None when no anomaly present (do NOT fabricate)
# emit(result: TriageResult, target: str = "-") -> None
#     target: "-" = stdout ; a filesystem path = write file ; "http(s)://..." = POST
```

## Evaluation (`eval/run_eval.py` — Group A)
Golden set = 10–20 known-bad lines from Loghub HDFS/Linux, hand-labelled. Report three numbers: **JSON-valid rate** (~100% expected), **correct-line localization**, **severity accuracy**. This is both the regression guard and the demo slide.

## Edge cases to harden (Group B harness)
empty file · file with no error (→ `None`, no hallucination) · truncated/garbled lines · multiple fatals (**policy: report the FIRST fatal**, document it) · non-UTF-8 bytes (read with `errors="replace"`) · huge file (chunking keeps memory flat).
