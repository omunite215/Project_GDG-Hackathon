"""Triage via the local Gemma model.

`triage()` hands a log excerpt to Ollama with constrained decoding
(``format=TriageResult.model_json_schema()`` + ``temperature=0``) so the model cannot emit
invalid JSON, then validates the response back into a `TriageResult`.

"No real error" is signalled by `error_severity == "INFO"` (constrained decoding forces a
complete result, so the model can't return nothing) — `triage()` maps that to `None`.

See docs/TRD.md (stack + contract) and docs/GROUP_A_Om_Pranav.md.
"""

import os

import ollama
from pydantic import ValidationError

from rawlog_triage.schema import TriageResult

DEFAULT_MODEL = "gemma3:4b"

SYSTEM_PROMPT = (
    "You are a log triage engine. Given a log excerpt, identify the single most severe "
    "anomalous or fatal event and fill the schema. If the excerpt shows only benign, normal "
    "activity, set error_severity to INFO. Use the timestamp from the chosen line, or '' if "
    "none is present. Be specific and concise in suggested_remediation."
)


def _client() -> ollama.Client:
    """Ollama client honoring OLLAMA_HOST, but normalizing the un-connectable 0.0.0.0 bind
    address to loopback. A real remote host (e.g. Group B → Group A's machine) is respected.
    """
    host = os.environ.get("OLLAMA_HOST", "").strip()
    if not host or "0.0.0.0" in host:
        host = "127.0.0.1:11434"
    return ollama.Client(host=host)


def _unparseable() -> TriageResult:
    """Typed fallback when the model returns unvalidatable output twice (defensive only)."""
    return TriageResult(
        service_name="unparseable",
        timestamp="",
        error_severity="ERROR",
        suggested_remediation=(
            "Triage model returned output that failed schema validation twice; "
            "inspect the log chunk manually."
        ),
    )


def triage(chunk: str, model: str = DEFAULT_MODEL) -> TriageResult | None:
    """Isolate the most severe event in `chunk` into a TriageResult, or None if no incident.

    Returns None when the excerpt has no real error (severity INFO). Never raises on bad
    model output and never returns invalid JSON: one bounded retry, then a typed sentinel.
    """
    client = _client()
    for _ in range(2):  # 1 attempt + 1 retry  # ponytail: 1 retry only
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chunk},
            ],
            format=TriageResult.model_json_schema(),
            options={"temperature": 0},
        )
        try:
            result = TriageResult.model_validate_json(response["message"]["content"])
        except ValidationError:
            continue
        return None if result.error_severity == "INFO" else result
    return _unparseable()


if __name__ == "__main__":
    # Self-check: run the live model on the known-bad FATAL line and assert a real incident.
    from pathlib import Path

    sample = Path(__file__).resolve().parents[2] / "data" / "sample.log"
    fatal_line = next(
        line for line in sample.read_text(encoding="utf-8").splitlines() if "FATAL" in line
    )
    out = triage(fatal_line)
    assert isinstance(out, TriageResult), f"expected TriageResult, got {out!r}"
    assert out.error_severity != "INFO", f"expected a real incident, got INFO: {out!r}"
    print(out.model_dump_json(indent=2))
