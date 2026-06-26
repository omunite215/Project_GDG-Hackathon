"""Smoke test: the package imports and exposes a version.

Keeps `pytest` green (exit 0) during Phase 0 scaffolding.
"""

import rawlog_triage


def test_package_importable_and_versioned() -> None:
    assert rawlog_triage.__version__
