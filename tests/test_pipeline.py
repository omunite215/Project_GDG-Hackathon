import json

from rawlog_triage import cli
from rawlog_triage.cli import EXIT_INPUT, EXIT_OK, EXIT_RUNTIME, main
from rawlog_triage.emit import emit
from rawlog_triage.ingest import CHUNK_MAX_CHARS, ingest
from rawlog_triage.schema import TriageResult

# --- ingest: pre-filter + edge cases ---------------------------------------


def test_ingest_filters_benign_lines_and_keeps_error(tmp_path) -> None:
    log_path = tmp_path / "sample.log"
    log_path.write_text("INFO boot completed\nERROR disk full\n", encoding="utf-8")

    chunks = ingest(str(log_path))

    assert chunks == ["ERROR disk full"]


def test_empty_file_returns_no_chunks(tmp_path) -> None:
    log_path = tmp_path / "empty.log"
    log_path.write_text("", encoding="utf-8")

    assert ingest(str(log_path)) == []


def test_ingest_handles_non_utf8_bytes(tmp_path) -> None:
    log_path = tmp_path / "garbled.log"
    log_path.write_bytes(b"\x80\x81\nERROR disk full\n")

    chunks = ingest(str(log_path))

    assert chunks == ["ERROR disk full"]


def test_ingest_keeps_truncated_garbled_lines(tmp_path) -> None:
    # A truncated line with no severity keyword must survive (recall-first):
    # it could itself be the anomaly. Only INFO/DEBUG-prefixed noise is dropped.
    log_path = tmp_path / "truncated.log"
    log_path.write_text(
        "INFO healthy\n2026-06-26T11:40:12Z auth-service connection po\n",
        encoding="utf-8",
    )

    chunks = ingest(str(log_path))

    assert chunks == ["2026-06-26T11:40:12Z auth-service connection po"]


def test_ingest_preserves_order_first_fatal_first(tmp_path) -> None:
    # Policy: report the FIRST fatal. ingest must preserve file order so the
    # earliest fatal lands ahead of later ones in chunks[0].
    log_path = tmp_path / "multi_fatal.log"
    log_path.write_text(
        "FATAL alpha pool exhausted\nERROR beta retry\nFATAL gamma oom\n",
        encoding="utf-8",
    )

    chunks = ingest(str(log_path))

    assert chunks[0].splitlines()[0] == "FATAL alpha pool exhausted"
    assert chunks[0].index("FATAL alpha") < chunks[0].index("FATAL gamma")


def test_ingest_chunks_large_file_keeping_memory_bounded(tmp_path) -> None:
    # Guards the flush fix: a long run of non-anomaly candidate lines must still
    # flush mid-stream into bounded chunks (the old code buffered them forever).
    log_path = tmp_path / "huge.log"
    lines = [f"heartbeat tick {i} processed request ok" for i in range(400)]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    chunks = ingest(str(log_path))

    assert len(chunks) > 1  # proves the buffer flushed before EOF
    assert all(len(c) <= CHUNK_MAX_CHARS + 64 for c in chunks)  # each stays bounded
    assert sum(c.count("\n") + 1 for c in chunks) == 400  # no lines lost


# --- emit -------------------------------------------------------------------


def test_emit_writes_schema_json_to_file(tmp_path) -> None:
    result = TriageResult(
        service_name="auth",
        timestamp="2026-06-26T12:00:00Z",
        error_severity="FATAL",
        suggested_remediation="Restart the auth service",
    )
    out_path = tmp_path / "result.json"

    emit(result, str(out_path))

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload == {
        "service_name": "auth",
        "timestamp": "2026-06-26T12:00:00Z",
        "error_severity": "FATAL",
        "suggested_remediation": "Restart the auth service",
    }


# --- CLI orchestration + failure paths --------------------------------------


def test_cli_reports_first_candidate_end_to_end(tmp_path, capsys, monkeypatch) -> None:
    # triage is mocked (the real one calls Ollama); this tests the CLI wiring:
    # ingest -> triage(first chunk, model) -> emit one valid JSON object.
    log_path = tmp_path / "logs.log"
    log_path.write_text(
        "INFO boot\nFATAL alpha pool exhausted\nERROR beta\nFATAL gamma oom\n",
        encoding="utf-8",
    )
    incident = TriageResult(
        service_name="auth-service",
        timestamp="2026-06-26T11:40:12Z",
        error_severity="FATAL",
        suggested_remediation="Increase the DB connection pool; restart auth-service.",
    )
    seen: dict[str, object] = {}

    def fake_triage(chunk, model="gemma3:4b"):
        seen["chunk"] = chunk
        seen["model"] = model
        return incident

    monkeypatch.setattr(cli, "triage", fake_triage)

    code = main([str(log_path), "--model", "gemma3:12b"])

    out = capsys.readouterr().out
    assert code == EXIT_OK
    payload = json.loads(out)  # exactly one valid JSON object on stdout
    assert payload["error_severity"] == "FATAL"
    assert payload["service_name"] == "auth-service"
    # the earliest fatal is fed first, and --model is threaded through
    assert seen["chunk"].startswith("FATAL alpha pool exhausted")
    assert seen["model"] == "gemma3:12b"


def test_cli_no_incident_emits_nothing(tmp_path, capsys, monkeypatch) -> None:
    # No-fabrication: when triage finds no incident (None), nothing is emitted.
    log_path = tmp_path / "benign.log"
    log_path.write_text(
        "Server started on port 8080\nListening for connections\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "triage", lambda chunk, model="gemma3:4b": None)

    code = main([str(log_path)])

    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert captured.out == ""  # nothing fabricated


def test_cli_missing_file_exits_nonzero_with_stderr(tmp_path, capsys) -> None:
    missing = tmp_path / "does_not_exist.log"

    code = main([str(missing)])

    captured = capsys.readouterr()
    assert code == EXIT_INPUT
    assert captured.out == ""  # never a partial/malformed payload on stdout
    assert "cannot read" in captured.err


def test_cli_triage_failure_exits_nonzero(tmp_path, capsys, monkeypatch) -> None:
    # Stands in for Ollama-unavailable / model-missing: any triage error is
    # caught at the orchestration boundary -> clean stderr + non-zero exit.
    log_path = tmp_path / "logs.log"
    log_path.write_text("FATAL pool exhausted\n", encoding="utf-8")

    def boom(_chunk, model="gemma3:4b"):
        raise ConnectionError("ollama unreachable at localhost:11434")

    monkeypatch.setattr(cli, "triage", boom)

    code = main([str(log_path)])

    captured = capsys.readouterr()
    assert code == EXIT_RUNTIME
    assert captured.out == ""
    assert "triage failed" in captured.err
