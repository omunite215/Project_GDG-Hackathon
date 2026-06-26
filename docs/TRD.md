# TRD — RawLog Triage Pipeline

## Stack
| Concern | Choice | Notes |
|---|---|---|
| Language | Python ≥3.12 | `requires-python = ">=3.12"`. Dev machine runs 3.13.7 (compatible). |
| LLM runtime | Ollama (local) | No data leaves the machine. |
| Model (dev) | `gemma3:4b` | Fast iteration. **Run `ollama pull gemma3:4b` first** — not yet pulled. |
| Model (quality) | `gemma3:12b` | Higher-quality pass; `ollama pull gemma3:12b`. |
| Validation | Pydantic v2 | `schema.py` model is the source of truth. |
| Structured output | Ollama `format=<json schema>` + `temperature=0` | Deterministic, schema-constrained generation via the `ollama` Python client. |
| Lint/format | ruff | Must be clean before every commit (pre-commit hook). |
| Tests | pytest | `pythonpath=["src"]`, smoke test in Phase 0. |

> Note: only `gemma2:2b`, `qwen2.5:14b`, `llama3.2:3b`, `nomic-embed-text` are pulled
> locally today. `gemma2:2b` can serve as a stopgap for early triage smoke tests, but the
> committed default is `gemma3:4b`.

## Architecture: `ingest → triage → emit`
A linear three-stage pipeline orchestrated by the CLI. Each stage is a module under
`src/rawlog_triage/`.

```
stdin / file path
      │
      ▼
  ingest.py   ──►  normalized raw log text (str)
      │
      ▼
  triage.py   ──►  TriageResult (validated Pydantic model)
      │            (Ollama call: gemma3, temperature=0, format=schema)
      ▼
  emit.py     ──►  JSON string (the EXACT 4-field object) → stdout / webhook
```

### Module contract
| Module | Responsibility | Input | Output |
|---|---|---|---|
| `schema.py` | Define `TriageResult` (4 fields) + `error_severity` enum. Provides the JSON schema for Ollama. | — | Pydantic model / JSON schema |
| `ingest.py` | Read & normalize raw logs. No interpretation. | file path or stdin | `str` (raw log text) |
| `triage.py` | Call Ollama to isolate the fatal line and fill the model. | raw log text `str`, model name | `TriageResult` |
| `emit.py` | Serialize the validated model to the 4-field JSON. | `TriageResult` | JSON `str` (and/or webhook POST) |
| `cli.py` | Parse args, wire `ingest → triage → emit`, handle exit codes. | argv | process exit code |

### Determinism & validation rules
- Every Ollama call sets `temperature=0` and passes the schema via `format=`.
- The model output is parsed back through Pydantic; validation failure ⇒ non-zero exit
  with a clear message, **never** malformed JSON on stdout.
- `emit.py` writes exactly one JSON object — the 4 fields, nothing else.

## Repo layout
`src/` layout, installed editable (`pip install -e .[dev]`). Package `rawlog_triage`
exposes a `rawlog-triage` console script (`cli:main`). Tests in `tests/`, sample logs in
`data/`, eval cases in `eval/`.

## Out of scope (this is a TRD, not a roadmap)
Streaming/tailing, log persistence, multiple simultaneous incidents, non-Ollama backends.
