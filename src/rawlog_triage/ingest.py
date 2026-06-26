"""Read raw logs and pre-filter likely-benign lines before triage.

Streaming, recall-first pre-filter: iterate the source line-by-line and drop only
the obvious high-volume noise (blank lines, replacement-char garbage, and
INFO/DEBUG/TRACE/NOTICE-prefixed lines). Everything else is kept as a candidate
and buffered into bounded chunks, so memory stays flat on huge files. The path
"-" reads stdin instead of a file.

# ponytail: recall-first is deliberate. triage() is the precise filter and must
# return None on a benign chunk (TRD "no fabrication"); ingest only strips the
# cheap, obvious noise so a keyword-less anomaly or a truncated/garbled line is
# never silently dropped before the model sees it. Stdlib re, no parser dep.
"""

from __future__ import annotations

import io
import re
import sys
from contextlib import nullcontext

CHUNK_MAX_CHARS = 2000

BENIGN_PREFIX_RE = re.compile(r"^\s*(INFO|DEBUG|TRACE|NOTICE)\b", re.IGNORECASE)


def _open_source(path: str):
    """Context manager yielding a text line iterator for a file path or '-' (stdin).

    Decodes with errors="replace" so non-UTF-8 bytes never crash ingestion, and
    streams line-by-line (memory stays flat) for both files and piped input.
    """
    if path != "-":
        return open(path, encoding="utf-8", errors="replace")
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is not None:  # real stdin: decode its bytes the same way as a file
        return nullcontext(io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"))
    return nullcontext(sys.stdin)  # already-text stream (e.g. a test's StringIO)


def ingest(path: str) -> list[str]:
    """Return ordered candidate log chunks (benign noise dropped) for triage.

    `path` is a file path, or "-" to read from stdin.
    """
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_chars = 0

    with _open_source(path) as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            # Drop blank lines and replacement-char-only garbage.
            if not stripped or stripped.replace("�", "").strip() == "":
                continue
            # Drop the high-volume benign noise; keep everything else as a candidate.
            if BENIGN_PREFIX_RE.match(stripped):
                continue

            buffer.append(stripped)
            buffer_chars += len(stripped) + 1  # +1 for the joining newline
            # Flush at the size bound regardless of line shape, so memory stays
            # flat even on a long run of non-anomaly candidate lines.
            if buffer_chars >= CHUNK_MAX_CHARS:
                chunks.append("\n".join(buffer))
                buffer = []
                buffer_chars = 0

    if buffer:
        chunks.append("\n".join(buffer))
    return chunks


# Severity-keyword ranks for cheap, deterministic candidate selection (rank 1 = none).
_SEVERITY_PATTERNS = [
    (4, re.compile(r"\b(FATAL|PANIC|EMERG(?:ENCY)?|CRIT(?:ICAL)?|ALERT)\b", re.IGNORECASE)),
    (3, re.compile(r"\b(ERROR|ERR|SEVERE|EXCEPTION|FAIL(?:ED|URE)?|TRACEBACK)\b", re.IGNORECASE)),
    (2, re.compile(r"\b(WARN(?:ING)?)\b", re.IGNORECASE)),
]


def _rank(line: str) -> int:
    for rank, pattern in _SEVERITY_PATTERNS:
        if pattern.search(line):
            return rank
    return 1


def select_candidate(chunks: list[str]) -> str | None:
    """Pick the single most-severe candidate line for triage — one O(N) pass, no model.

    Keeps the model cost at exactly one call regardless of log size: scan the pre-filtered
    candidates, return the *earliest* line at the highest severity rank (FATAL > ERROR > WARN),
    short-circuiting on the first FATAL. With no severity keyword, fall back to the first
    candidate line (recall: a keyword-less anomaly still reaches the model, which may return
    None). Returns None only when there are no candidate lines.
    """
    best_line: str | None = None
    best_rank = 0
    first_line: str | None = None
    for chunk in chunks:
        for raw in chunk.split("\n"):
            line = raw.strip()
            if not line:
                continue
            if first_line is None:
                first_line = line
            rank = _rank(line)
            if rank > best_rank:
                best_rank, best_line = rank, line
                if rank == 4:  # FATAL — earliest one wins; nothing can outrank it
                    return best_line
    return best_line if best_rank >= 2 else first_line
