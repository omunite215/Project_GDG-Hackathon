"""Read raw logs and pre-filter likely-benign lines before triage.

Streaming, recall-first pre-filter: iterate the file line-by-line and drop only
the obvious high-volume noise (blank lines, replacement-char garbage, and
INFO/DEBUG/TRACE/NOTICE-prefixed lines). Everything else is kept as a candidate
and buffered into bounded chunks, so memory stays flat on huge files.

# ponytail: recall-first is deliberate. triage() is the precise filter and must
# return None on a benign chunk (TRD "no fabrication"); ingest only strips the
# cheap, obvious noise so a keyword-less anomaly or a truncated/garbled line is
# never silently dropped before the model sees it. Stdlib re, no parser dep.
"""

from __future__ import annotations

import re

CHUNK_MAX_CHARS = 2000

BENIGN_PREFIX_RE = re.compile(r"^\s*(INFO|DEBUG|TRACE|NOTICE)\b", re.IGNORECASE)


def ingest(path: str) -> list[str]:
    """Return ordered candidate log chunks (benign noise dropped) for triage."""
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_chars = 0

    with open(path, encoding="utf-8", errors="replace") as handle:
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
