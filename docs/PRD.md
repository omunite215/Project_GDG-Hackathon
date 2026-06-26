# PRD — RawLog Triage Pipeline

## Problem
On-call and ops engineers face walls of raw log output when something breaks. The
single fatal/anomalous line that explains the incident is buried among hundreds of
benign INFO/DEBUG lines. Manually finding it and turning it into a structured,
actionable alert is slow and inconsistent.

## Solution
A small Python utility that takes a raw log blob, uses a **local** Gemma model (via
Ollama — no data leaves the machine) to isolate the single most anomalous/fatal line,
and emits a structured, schema-validated JSON object that can be POSTed straight to a
webhook (Slack, PagerDuty, an incident bot, etc.).

## Users
- On-call / SRE / ops engineers triaging an incident.
- Automated alerting glue that needs structured input rather than raw text.

## Inputs
- Raw, multi-line log text, supplied either as a **file path** or piped via **stdin**.
- No assumption about log format; the model reasons over plain text.

## Output — the EXACT contract (4 fields, no more, no fewer)
A single JSON object:

| Field | Type | Meaning |
|---|---|---|
| `service_name` | string | The service/component the fatal line came from (e.g. `auth-service`). |
| `timestamp` | string | The timestamp of the isolated fatal line, as it appears in the log. |
| `error_severity` | string (enum) | One of: `CRITICAL`, `FATAL`, `ERROR`, `WARNING`, `INFO`. |
| `suggested_remediation` | string | A concise, actionable next step to resolve the issue. |

Example:
```json
{
  "service_name": "auth-service",
  "timestamp": "2026-06-26T11:40:12Z",
  "error_severity": "FATAL",
  "suggested_remediation": "Increase the DB connection pool size or fix the connection leak; restart auth-service."
}
```

This object is defined by the Pydantic model in `src/rawlog_triage/schema.py`, which is
also the JSON schema given to Ollama via `format=`. The enum values are finalized in the
schema phase.

## Success criteria
1. **Always valid:** 100% of runs emit JSON that validates against the schema (4 fields,
   correct types, valid enum) — or exit non-zero with a clear error, never malformed JSON.
2. **Correct isolation:** On the eval set (`eval/`), the pipeline identifies the intended
   fatal/anomalous line.
3. **Deterministic:** Same input + same model ⇒ same output (`temperature=0`).
4. **Local & fast:** Runs entirely on a local Ollama model; `gemma3:4b` is the dev default.
5. **Webhook-ready:** Output is a single JSON object on stdout, directly POST-able.

## Non-goals
- No multi-line incident summaries (one fatal line → one object).
- No log storage, indexing, or streaming/tailing.
- No cloud LLM calls.
