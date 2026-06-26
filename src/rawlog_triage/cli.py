"""Command-line entry point for the rawlog triage pipeline."""

from __future__ import annotations

import argparse
import sys

from rawlog_triage.emit import emit
from rawlog_triage.ingest import ingest, select_candidate
from rawlog_triage.triage import triage

# Exit codes: 0 ok (incident or clean no-op); 2 bad input (unreadable file);
# 1 runtime failure (triage/model/emit). Errors go to stderr only — stdout
# carries the JSON payload or nothing, never a partial/malformed object.
EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_INPUT = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triage-logs")
    parser.add_argument("input", help="Path to the raw log file to inspect")
    parser.add_argument(
        "--target",
        default="-",
        help="Output target: '-' for stdout, a path, or an http(s) URL",
    )
    parser.add_argument(
        "--model",
        default="gemma3:4b",
        help="Ollama model name passed to triage()",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        chunks = ingest(args.input)
    except OSError as exc:
        print(f"triage-logs: cannot read {args.input!r}: {exc}", file=sys.stderr)
        return EXIT_INPUT

    # Cheap O(N) pass picks the single most-severe candidate line, so the model is
    # called exactly once regardless of log size (and the earliest FATAL anywhere in
    # the file is found, not just in the first chunk).
    candidate = select_candidate(chunks)
    if candidate is None:
        return EXIT_OK

    try:
        result = triage(candidate, model=args.model)
    except Exception as exc:  # Ollama unavailable, model missing, etc.
        print(f"triage-logs: triage failed: {exc}", file=sys.stderr)
        return EXIT_RUNTIME

    if result is None:
        return EXIT_OK

    try:
        emit(result, args.target)
    except Exception as exc:
        print(f"triage-logs: emit failed: {exc}", file=sys.stderr)
        return EXIT_RUNTIME

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
