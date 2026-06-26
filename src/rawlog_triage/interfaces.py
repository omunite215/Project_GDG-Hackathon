"""Integration contract between Group A (triage) and Group B (pipeline).

Signatures only — the seam both pairs code against. Real implementations live in
``ingest.py`` / ``triage.py`` / ``emit.py``. Do not change a signature here without
telling the other pair (see docs/TRD.md).
"""

from rawlog_triage.schema import TriageResult

__all__ = ["TriageResult", "emit", "ingest", "triage"]


def ingest(path: str) -> list[str]:
    """Read a raw log file, chunk it, and pre-filter benign lines → candidate chunks."""
    ...


def triage(chunk: str) -> TriageResult | None:
    """Gemma structured-output call. Returns None when the chunk has no real error."""
    ...


def emit(result: TriageResult, target: str = "-") -> None:
    """Write the result: ``"-"`` → stdout, a path → file, ``http(s)://…`` → POST."""
    ...
