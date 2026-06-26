# PRD.md — RawLog Triage Pipeline

## Problem
Production systems emit gigabytes of unstructured logs. Finding the one line that actually failed means manual regex spelunking and filtering. We automate the triage: raw log in, one structured incident record out.

## Users
- **The on-call engineer** who needs the failing event extracted and explained, fast.
- **The downstream system** (webhook → DB / alerting) that needs clean, valid JSON it can ingest without parsing surprises.

## Core requirement (the deliverable)
A local CLI/script that reads a raw log text stream and returns **one** syntactically perfect, schema-validated JSON object:

| field | type | notes |
|---|---|---|
| `service_name` | string | service/component that emitted the failing line |
| `timestamp` | string | ISO-8601, or `""` if none present |
| `error_severity` | enum | `INFO` \| `WARNING` \| `ERROR` \| `FATAL` |
| `suggested_remediation` | string | one concrete next step to investigate/fix |

Output is ready for webhook injection (POST) or write-to-file.

## Inputs
Raw logs from the **Loghub** repo (HDFS or Linux folder), a ~500KB sample saved as `data/sample_production_logs.txt`. Organizers may hand unseen samples during the hardening window.

## Success criteria (this is also the demo)
1. **Valid JSON 100% of the time** (guaranteed by constrained decoding).
2. Correctly **isolates the anomalous/fatal line** on the golden set.
3. Correct **severity** + a plausible **remediation**.
4. **Handles edge cases without crashing or hallucinating:** empty file; file with NO error (returns nothing — must not invent one); truncated lines; multiple errors; non-UTF-8 bytes.
5. Runs **end-to-end on one command** in front of judges.

## Scope / non-goals
- **NO** model training / fine-tuning. Inference only.
- **NO** database. **NO** web UI.
- The "PR creator / merger" framing from the original notes belongs to a *different* track — **out of scope** unless organizers say otherwise. (If they do: stretch goal = POST the triage JSON as a structured comment to a webhook/Slack.)

## Timeline
Event is **today, Jun 26, 9:00 AM–7:00 PM EDT**, in person at Curry Student Center, Northeastern. Real build time ≈ 6–7 hrs. **Lock a submittable end-to-end version ~2 hours before close**, then spend remaining time on golden-set metrics and demo polish — not new features.
