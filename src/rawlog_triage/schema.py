"""Output schema for the triage pipeline.

`TriageResult` is the EXACT 4-field webhook payload and the single source of truth for the
contract. It is also the JSON schema handed to Ollama via
``format=TriageResult.model_json_schema()`` with ``temperature=0`` so constrained decoding
makes invalid JSON impossible.

See docs/PRD.md (output contract) and docs/TRD.md (stack).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["INFO", "WARNING", "ERROR", "FATAL"]


class TriageResult(BaseModel):
    """The single structured incident record emitted per run."""

    # The 4-field contract is sacred: reject anything extra so the payload stays exact and
    # the generated JSON schema carries `additionalProperties: false` for Ollama.
    model_config = ConfigDict(extra="forbid")

    service_name: str = Field(description="Service/component that emitted the failing line")
    timestamp: str = Field(description="ISO-8601 timestamp of the event, or '' if none present")
    error_severity: Severity = Field(
        description="Severity of the isolated line: one of INFO, WARNING, ERROR, FATAL"
    )
    suggested_remediation: str = Field(
        description="One concrete next step to investigate or fix the issue"
    )
