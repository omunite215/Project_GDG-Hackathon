"""Command-line entry point.

Will wire ingest -> triage -> emit. For now this is a Phase 0 placeholder so the
``rawlog-triage`` console script resolves to a valid callable.

See tasks/todo.md.
"""


def main() -> int:
    """Phase 0 placeholder. Real ingest -> triage -> emit wiring lands later."""
    print("rawlog-triage: scaffold only - see tasks/todo.md")
    return 0


# TODO(phase-orchestration): wire ingest -> triage -> emit and parse CLI args.

if __name__ == "__main__":
    raise SystemExit(main())
