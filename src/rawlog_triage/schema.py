"""Output schema for the triage pipeline.

Will define the Pydantic v2 model for the EXACT 4-field webhook payload:
service_name, timestamp, error_severity, suggested_remediation. This model is
also the JSON schema handed to Ollama via ``format=`` for structured outputs.

See docs/PRD.md (output contract) and docs/TRD.md (stack).
"""

# TODO(phase-schema): define the Pydantic v2 TriageResult model + error_severity enum.
