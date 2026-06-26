"""Tests for the TriageResult output contract (the sacred 4-field payload)."""

import pytest
from pydantic import ValidationError

from rawlog_triage.schema import TriageResult

VALID = {
    "service_name": "auth-service",
    "timestamp": "2026-06-26T11:40:12Z",
    "error_severity": "FATAL",
    "suggested_remediation": "Increase the DB connection pool size; restart auth-service.",
}


def test_valid_payload_constructs_and_round_trips():
    result = TriageResult(**VALID)
    assert result.model_dump() == VALID


def test_missing_field_fails():
    payload = {k: v for k, v in VALID.items() if k != "timestamp"}
    with pytest.raises(ValidationError):
        TriageResult(**payload)


def test_extra_field_fails():
    with pytest.raises(ValidationError):
        TriageResult(**VALID, source_host="db-01")


def test_bad_enum_fails():
    payload = {**VALID, "error_severity": "FATALITY"}
    with pytest.raises(ValidationError):
        TriageResult(**payload)


def test_json_schema_is_exactly_four_fields_and_closed():
    schema = TriageResult.model_json_schema()
    assert set(schema["properties"]) == {
        "service_name",
        "timestamp",
        "error_severity",
        "suggested_remediation",
    }
    # extra="forbid" → Ollama constrained decoding cannot emit stray keys.
    assert schema["additionalProperties"] is False
