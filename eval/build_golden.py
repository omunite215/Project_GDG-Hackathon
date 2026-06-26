"""Build a labelled golden set from the LogHub 2k structured CSVs.

Reads `eval/loghub/*_structured.csv` (run `fetch_loghub.py` first), auto-detects each dataset's
`Level`/`Label` columns, maps levels to our 4 severity buckets, samples class-balanced cases,
assigns a deterministic dev/test split, and writes `eval/golden_loghub.jsonl`.

Case kinds:
  severity   - has `expected_severity` (+ derived `expect_incident`); scored on severity & detection
  detection  - has `expect_incident` from the anomaly Label (BGL); scored on detection only
  spotcheck  - no labels; only a valid-JSON rate is reported

Run:  python eval/build_golden.py
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path

LOGHUB = Path(__file__).with_name("loghub")
OUT = Path(__file__).with_name("golden_loghub.jsonl")

CATEGORY = {
    "HDFS": "Distributed systems",
    "Hadoop": "Distributed systems",
    "Spark": "Distributed systems",
    "Zookeeper": "Distributed systems",
    "OpenStack": "Distributed systems",
    "BGL": "Supercomputers",
    "HPC": "Supercomputers",
    "Thunderbird": "Supercomputers",
    "Windows": "Operating systems",
    "Linux": "Operating systems",
    "Mac": "Operating systems",
    "Android": "Mobile systems",
    "HealthApp": "Mobile systems",
    "Apache": "Server applications",
    "OpenSSH": "Server applications",
    "Proxifier": "Standalone software",
}

LEVEL_TO_BUCKET = {
    "info": "INFO",
    "notice": "INFO",
    "debug": "INFO",
    "trace": "INFO",
    "verbose": "INFO",
    "fine": "INFO",
    "finer": "INFO",
    "finest": "INFO",
    "config": "INFO",
    "stat": "INFO",
    "stats": "INFO",
    "i": "INFO",
    "d": "INFO",
    "v": "INFO",
    "n": "INFO",
    "warn": "WARNING",
    "warning": "WARNING",
    "w": "WARNING",
    "error": "ERROR",
    "err": "ERROR",
    "severe": "ERROR",
    "e": "ERROR",
    "fatal": "FATAL",
    "critical": "FATAL",
    "crit": "FATAL",
    "emerg": "FATAL",
    "emergency": "FATAL",
    "alert": "FATAL",
    "panic": "FATAL",
    "f": "FATAL",
}

# Dynamic fallbacks so ANY dataset's level vocabulary maps without hardcoding it.
_SUBSTRING_RULES = [
    (("fatal", "panic", "emerg", "crit", "alert"), "FATAL"),
    (("err", "severe", "fail", "exception"), "ERROR"),
    (("warn",), "WARNING"),
    (("info", "debug", "trace", "notice", "verbose", "fine", "config", "normal", "stat"), "INFO"),
]
_CHAR_MAP = {
    "f": "FATAL",
    "e": "ERROR",
    "w": "WARNING",
    "i": "INFO",
    "d": "INFO",
    "v": "INFO",
    "n": "INFO",
    "t": "INFO",
}
_BENIGN_LABELS = {"-", "", "normal", "ok", "false", "0", "none", "info", "benign"}


def normalize_level(token: str) -> str | None:
    """Map an arbitrary source level token to our canonical bucket (data-driven)."""
    t = (token or "").strip().lower()
    if not t:
        return None
    if t in LEVEL_TO_BUCKET:
        return LEVEL_TO_BUCKET[t]
    for needles, bucket in _SUBSTRING_RULES:
        if any(n in t for n in needles):
            return bucket
    if len(t) == 1 and t in _CHAR_MAP:
        return _CHAR_MAP[t]
    return None


COMPONENT_COLS = ["Component", "Process", "Program", "Node", "Location", "Type"]
PER_BUCKET = 10  # severity cases sampled per (dataset, bucket)
DETECTION_N = 10  # alert + normal cases for label-based detection (BGL)
SPOTCHECK_N = 6


def _col(cols: list[str], *names: str) -> str | None:
    lookup = {c.lower(): c for c in cols}
    for n in names:
        if n in lookup:
            return lookup[n]
    return None


def _chunk(row: dict, level_col: str | None, comp_col: str | None) -> str:
    parts = []
    if level_col and row.get(level_col):
        parts.append(row[level_col])
    if comp_col and row.get(comp_col):
        parts.append(row[comp_col])
    head = " ".join(parts)
    content = (row.get("Content") or "").strip()
    return f"{head}: {content}".strip(": ").strip() if head else content


def build() -> list[dict]:
    cases: list[dict] = []
    print(f"{'dataset':<14}{'category':<22}{'kind':<22}cases")
    print("-" * 70)
    for path in sorted(LOGHUB.glob("*_2k.log_structured.csv")):
        dataset = path.name.split("_2k")[0]
        category = CATEGORY.get(dataset, "Unknown")
        rng = random.Random(f"loghub-{dataset}")
        with path.open(encoding="utf-8", errors="replace") as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) if rows else []
        level_col = _col(cols, "level")
        label_col = _col(cols, "label", "alert")
        comp_col = _col(cols, *[c.lower() for c in COMPONENT_COLS])

        # Auto-discover the dataset's level vocabulary; map each value dynamically. A Level
        # column is "usable" only if >=80% of values resolve to a bucket (rejects bogus
        # columns like Linux's "combo").
        buckets: dict[str, list[dict]] = {}
        vocab: Counter = Counter()
        vocab_map: dict[str, str | None] = {}
        if level_col:
            mapped = 0
            for row in rows:
                raw = (row.get(level_col) or "").strip()
                vocab[raw] += 1
                if raw not in vocab_map:
                    vocab_map[raw] = normalize_level(raw)
                if vocab_map[raw]:
                    mapped += 1
                    buckets.setdefault(vocab_map[raw], []).append(row)
            if mapped < 0.8 * len(rows):
                buckets = {}
                vocab_map = dict.fromkeys(vocab_map, None)

        dataset_cases: list[dict] = []

        if buckets:  # severity-scorable (incl. single-class INFO = no-fabrication check)
            for bucket, group in buckets.items():
                rng.shuffle(group)
                for row in group[:PER_BUCKET]:
                    dataset_cases.append(
                        {
                            "kind": "severity",
                            "chunk": _chunk(row, level_col, comp_col),
                            "expected_severity": bucket,
                            "expect_incident": bucket != "INFO",
                        }
                    )

        # Label-based anomaly detection (needs both alert and normal rows present).
        if label_col:
            alerts = [
                r for r in rows if (r.get(label_col) or "").strip().lower() not in _BENIGN_LABELS
            ]
            normals = [
                r for r in rows if (r.get(label_col) or "").strip().lower() in _BENIGN_LABELS
            ]
            if alerts and normals:
                rng.shuffle(alerts)
                rng.shuffle(normals)
                for row in alerts[:DETECTION_N]:
                    dataset_cases.append(
                        {
                            "kind": "detection",
                            "chunk": _chunk(row, level_col, comp_col),
                            "expect_incident": True,
                        }
                    )
                for row in normals[:DETECTION_N]:
                    dataset_cases.append(
                        {
                            "kind": "detection",
                            "chunk": _chunk(row, level_col, comp_col),
                            "expect_incident": False,
                        }
                    )

        if not dataset_cases:  # no usable labels → spot-check only
            sample = rng.sample(rows, min(SPOTCHECK_N, len(rows)))
            dataset_cases = [
                {"kind": "spotcheck", "chunk": _chunk(row, level_col, comp_col)} for row in sample
            ]

        # Deterministic dev/test split (50/50) within the dataset.
        rng.shuffle(dataset_cases)
        for i, case in enumerate(dataset_cases):
            case.update(
                {"dataset": dataset, "category": category, "split": "dev" if i % 2 == 0 else "test"}
            )
            cases.append(case)

        kinds = ",".join(sorted({c["kind"] for c in dataset_cases}))
        print(f"{dataset:<14}{category:<22}{kinds:<22}{len(dataset_cases)}")
        if vocab:
            shown = "  ".join(
                f"{(raw or '(blank)')}->{vocab_map.get(raw) or '?'}"
                for raw, _ in vocab.most_common(8)
            )
            print(f"               levels: {shown}")
    return cases


def main() -> int:
    if not LOGHUB.exists():
        print("eval/loghub/ missing — run: python eval/fetch_loghub.py")
        return 1
    cases = build()
    with OUT.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    print("-" * 70)
    print(f"wrote {len(cases)} cases -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
