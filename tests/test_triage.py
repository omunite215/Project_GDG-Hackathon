"""Hermetic tests for triage() — Ollama is mocked, so these never hit the real model."""

import json

from rawlog_triage import triage as triage_mod
from rawlog_triage.schema import TriageResult
from rawlog_triage.triage import triage

VALID_FATAL = json.dumps(
    {
        "service_name": "auth-service",
        "timestamp": "2026-06-26T11:40:12Z",
        "error_severity": "FATAL",
        "suggested_remediation": "Increase the DB connection pool; restart auth-service.",
    }
)
VALID_INFO = json.dumps(
    {
        "service_name": "auth-service",
        "timestamp": "",
        "error_severity": "INFO",
        "suggested_remediation": "No action needed.",
    }
)
INVALID = '{"nope": true}'  # valid JSON, wrong schema → ValidationError


class _FakeClient:
    """Stands in for ollama.Client; .chat() yields the queued message contents in order."""

    def __init__(self, contents):
        self._it = iter(contents)

    def chat(self, **kwargs):
        return {"message": {"content": next(self._it)}}


def _patch_client(monkeypatch, *contents):
    client = _FakeClient(contents)
    monkeypatch.setattr(triage_mod, "_client", lambda: client)


def test_valid_response_returns_result(monkeypatch):
    _patch_client(monkeypatch, VALID_FATAL)
    result = triage("2026-... FATAL connection pool exhausted")
    assert isinstance(result, TriageResult)
    assert result.error_severity == "FATAL"
    assert result.service_name == "auth-service"


def test_info_severity_returns_none(monkeypatch):
    _patch_client(monkeypatch, VALID_INFO)
    assert triage("2026-... INFO health check ok") is None


def test_invalid_then_valid_retries(monkeypatch):
    _patch_client(monkeypatch, INVALID, VALID_FATAL)
    result = triage("anything")
    assert isinstance(result, TriageResult)
    assert result.error_severity == "FATAL"


def test_both_invalid_returns_unparseable_sentinel(monkeypatch):
    _patch_client(monkeypatch, INVALID, INVALID)
    result = triage("anything")
    assert isinstance(result, TriageResult)
    assert result.service_name == "unparseable"
    assert result.error_severity == "ERROR"
