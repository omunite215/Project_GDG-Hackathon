# Testing Guide — RawLog Triage Pipeline

How to test the pipeline at every layer. Commands are PowerShell (the dev environment);
`make` equivalents are shown where they exist. Run from the repo root.

## Test layers at a glance

| Layer | Needs Ollama? | Command | What it proves |
|---|---|---|---|
| Lint / format | no | `ruff check .` · `ruff format --check .` | style + obvious errors; gate before every commit |
| Unit / hermetic | **no** | `pytest` | schema contract, triage logic (mocked), pipeline edge cases — fast & deterministic |
| Live self-check | yes | `python -m rawlog_triage.triage` | the real model + parse path works |
| End-to-end CLI | yes | `triage-logs <log>` | full `ingest → triage → emit` on real input |
| Accuracy / eval | yes | `python eval/run_eval.py` | JSON-valid %, detection %, severity accuracy |

> **Hermetic tests never touch Ollama** (the model is mocked), so `ruff` + `pytest` are the
> safe, fast suite to run anywhere (and what CI should run). The live layers need Ollama running
> with `gemma3:4b` pulled.

## 0. One-time setup
```powershell
./scripts/setup.ps1          # creates .venv, installs editable + dev (ruff, pytest)   (or: uv sync)
ollama pull gemma3:4b        # required only for the live layers
```
Activate the venv for ad-hoc commands: `.\.venv\Scripts\Activate.ps1` (or prefix with
`.\.venv\Scripts\python.exe -m ...`).

## 1. Lint & format (no Ollama)
```powershell
ruff check .            # → "All checks passed!"
ruff format --check .   # → "N files already formatted"
```
`make lint` / `./scripts/lint.ps1` do the same. The pre-commit hook runs both; commits fail if dirty.

## 2. Unit tests (no Ollama) — the everyday suite
```powershell
pytest                  # → 21 passed     (also: ./scripts/test.ps1  |  make test)
```
What's covered:
| File | Covers |
|---|---|
| `tests/test_smoke.py` | package imports + `__version__` |
| `tests/test_schema.py` | `TriageResult` contract: valid round-trip, missing/extra field → error, bad enum → error, schema is exactly 4 closed fields |
| `tests/test_triage.py` | `triage()` with a **mocked** Ollama client: valid → result, severity `INFO` → `None`, invalid-then-valid retry, both-invalid → `unparseable` sentinel |
| `tests/test_pipeline.py` | `ingest` / `emit` / `cli` edge cases (mocked `triage`): empty file, benign no-incident, garbled bytes, large-file chunking, CLI exit codes |

Useful selectors:
```powershell
pytest -v                       # per-test names
pytest tests/test_schema.py     # one file
pytest -k triage                # tests matching a keyword
```

## 3. Live triage self-check (needs Ollama)
```powershell
python -m rawlog_triage.triage
```
Runs the real `gemma3:4b` on the known-bad FATAL line in `data/sample.log` and asserts a non-INFO
`TriageResult`, then prints it. Good first check that Ollama + the model + parsing all work.

## 4. End-to-end CLI (needs Ollama)
```powershell
triage-logs data/sample.log
```
Expect a single line of JSON with exactly four keys and exit code 0:
```json
{"service_name":"auth-service","timestamp":"2026-06-26T11:40:12Z","error_severity":"FATAL","suggested_remediation":"..."}
```
Other modes:
```powershell
Get-Content data/sample.log | triage-logs                  # read from stdin
triage-logs data/sample.log --target out.json              # write to a file
triage-logs data/sample.log --target https://hooks.example.com/incident   # POST to a webhook
triage-logs data/sample.log --model gemma3:12b             # different model (must be pulled)
```
**Exit codes:** `0` success (incident emitted, or clean no-op) · `2` bad input (unreadable file) ·
`1` runtime failure (Ollama unreachable / model missing / emit error). stdout only ever carries the
JSON payload or nothing — never a partial object; errors go to stderr.

## 5. Accuracy / eval (needs Ollama)
```powershell
python eval/run_eval.py                 # defaults: --model gemma3:4b --golden eval/golden.jsonl
python eval/run_eval.py --model gemma3:12b   # compare a bigger model (pull it first)
```
Prints a per-case ✓/✗ table and three headline numbers. Current baseline on `gemma3:4b`:
**JSON-valid 10/10 (100%) · detection 10/10 (100%) · severity 7/8 (88%)**.
Add cases by appending JSON lines to `eval/golden.jsonl`:
```json
{"name":"my-case","expect_incident":true,"expected_severity":"ERROR","expected_service":"svc","chunk":"...log text..."}
{"name":"benign-case","expect_incident":false,"chunk":"...benign log text..."}
```

## 6. Manual edge cases (mostly no Ollama)
These exercise `ingest`/`cli` paths and don't call the model (benign/empty inputs are filtered first):
```powershell
triage-logs does-not-exist.log            # → stderr message, exit 2
"" | Set-Content C:\tmp\empty.log
triage-logs C:\tmp\empty.log              # → no output, exit 0
"INFO svc health ok" | Set-Content C:\tmp\benign.log
triage-logs C:\tmp\benign.log             # → no output, exit 0 (benign filtered; no fabrication)
```
A file containing a real `FATAL`/`ERROR` line (e.g. `data/sample.log`) does hit the model and emits JSON.

## 7. Troubleshooting
- **`ConnectionError: Failed to connect to Ollama`** — confirm the server is up (`ollama list` works)
  and the model is pulled (`ollama pull gemma3:4b`). If `OLLAMA_HOST` is set to `0.0.0.0:11434`, the
  client can't dial a bind address; the code normalizes it to `127.0.0.1`, but if you still hit it,
  set `$env:OLLAMA_HOST="127.0.0.1:11434"`. (See `docs/lessons.md`.)
- **`pytest` can't import `rawlog_triage`** — run `./scripts/setup.ps1` (editable install), or rely on
  the configured `pythonpath=["src"]`.
- **First live run is slow** — the model is loading into memory; subsequent calls are fast.
- **Non-ASCII looks garbled in the console** — cosmetic Windows code-page rendering; the JSON payload
  itself is correct.

## 8. CI note
CI should run the **offline** gate only: `ruff check .` + `ruff format --check .` + `pytest`
(the live/eval layers need Ollama and a pulled model). A CI workflow is not yet committed — see
`tasks/todo.md`.
