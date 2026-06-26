# RawLog Triage Pipeline

Reads raw server/system logs, uses a **local** Gemma model via Ollama to isolate the
single anomalous/fatal line, and emits a schema-validated JSON object ready for a webhook:

```json
{
  "service_name": "auth-service",
  "timestamp": "2026-06-26T11:40:12Z",
  "error_severity": "FATAL",
  "suggested_remediation": "Increase the DB connection pool size or fix the connection leak; restart auth-service."
}
```

## Quick start
```
./scripts/setup.ps1          # venv + install + git hook   (make setup)
ollama pull gemma3:4b        # dev model (required before triage)
rawlog-triage data/sample.log
```

## Docs
- [docs/PRD.md](docs/PRD.md) — problem, inputs, the exact 4-field output contract
- [docs/TRD.md](docs/TRD.md) — stack and the `ingest → triage → emit` contract
- [docs/instructions.md](docs/instructions.md) — setup / lint / test / run
- [tasks/todo.md](tasks/todo.md) — phase checklist
- [CLAUDE.md](CLAUDE.md) — project rules & workflow

> Status: **Phase 0 (scaffolding)**. Pipeline logic lands in later phases.
