"""Emit a triage result to stdout, a file, or an HTTP(S) endpoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from rawlog_triage.schema import TriageResult


def emit(result: TriageResult, target: str = "-") -> None:
    """Serialize the result as the exact 4-field JSON payload."""
    payload = result.model_dump(mode="json")
    body = json.dumps(payload, separators=(",", ":")) + "\n"

    if target == "-":
        sys.stdout.write(body)
        return

    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"}:
        request = Request(
            target,
            data=body.encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                response.read()
        except URLError as exc:
            raise RuntimeError(f"Failed to POST triage result: {exc}") from exc
        return

    output_path = Path(target)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")
