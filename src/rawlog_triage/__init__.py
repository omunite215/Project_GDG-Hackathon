"""RawLog Triage Pipeline.

Reads raw server/system logs, uses a local Gemma model via Ollama to isolate
the single anomalous/fatal line, and emits a schema-validated JSON object
(service_name, timestamp, error_severity, suggested_remediation) ready for a
webhook.

Pipeline contract: ingest -> triage -> emit. See docs/TRD.md.
"""

__version__ = "0.0.0"
