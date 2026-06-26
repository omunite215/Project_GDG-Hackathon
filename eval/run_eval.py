"""Evaluate triage() against a golden set and report accuracy.

Works with both golden files:
  - eval/golden.jsonl         (synthetic smoke set)
  - eval/golden_loghub.jsonl  (real LogHub data, grouped by category; built by build_golden.py)

Metrics (computed only where ground truth exists in each case):
  valid %      - result is None or a real TriageResult (not the unparseable sentinel)
  severity %   - predicted bucket == expected_severity   (predicted = INFO when triage returns None)
  detection %  - (result is not None) == expect_incident

Run (needs Ollama):
  python eval/run_eval.py                                            # synthetic set
  python eval/run_eval.py --golden eval/golden_loghub.jsonl --split test
  python eval/run_eval.py --golden eval/golden_loghub.jsonl --category "Mobile systems" --split dev
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from rawlog_triage.schema import TriageResult
from rawlog_triage.triage import triage

PASS = 90.0  # accuracy target per category (%)


def load_cases(path: str) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _is_valid(result: TriageResult | None) -> bool:
    if result is None:
        return True
    return result.service_name != "unparseable"


def _predicted_severity(result: TriageResult | None) -> str:
    return "INFO" if result is None else result.error_severity


def _pct(num: int, denom: int) -> str:
    return f"{100 * num / denom:.0f}%" if denom else "  -"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_eval")
    parser.add_argument("--golden", default=str(Path(__file__).with_name("golden.jsonl")))
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--category", default=None)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--limit", type=int, default=0, help="cap number of cases (0 = no cap)")
    args = parser.parse_args(argv)

    cases = load_cases(args.golden)
    if args.split != "all":
        cases = [c for c in cases if c.get("split", "all") in (args.split, "all")]
    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]
    if args.dataset:
        cases = [c for c in cases if c.get("dataset") == args.dataset]
    if args.limit:
        cases = cases[: args.limit]

    # group -> [valid_ok, valid_n, sev_ok, sev_n, det_ok, det_n]
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    for case in cases:
        result = triage(case["chunk"], model=args.model)
        group = case.get("category", "(synthetic)")
        s = stats[group]
        s[1] += 1
        s[0] += _is_valid(result)
        if "expected_severity" in case:
            s[3] += 1
            s[2] += _predicted_severity(result) == case["expected_severity"]
        if "expect_incident" in case:
            s[5] += 1
            s[4] += (result is not None) == case["expect_incident"]

    print(f"model: {args.model}   split: {args.split}   cases: {len(cases)}\n")
    print(f"{'category':<22}{'n':>4}  {'valid':>6}  {'severity':>12}  {'detection':>12}  ok")
    print("-" * 74)
    tot = [0, 0, 0, 0, 0, 0]
    for group in sorted(stats):
        v_ok, v_n, se_ok, se_n, de_ok, de_n = stats[group]
        for i, val in enumerate(stats[group]):
            tot[i] += val
        sev = f"{se_ok}/{se_n} ({_pct(se_ok, se_n)})" if se_n else "       -"
        det = f"{de_ok}/{de_n} ({_pct(de_ok, de_n)})" if de_n else "       -"
        ok = (
            "OK"
            if (se_n == 0 or 100 * se_ok / se_n >= PASS)
            and (de_n == 0 or 100 * de_ok / de_n >= PASS)
            and (se_n or de_n)
            else ("-" if not (se_n or de_n) else "X")
        )
        print(f"{group:<22}{v_n:>4}  {_pct(v_ok, v_n):>6}  {sev:>12}  {det:>12}  {ok}")
    print("-" * 74)
    print(
        f"{'OVERALL':<22}{tot[1]:>4}  {_pct(tot[0], tot[1]):>6}  "
        f"{tot[2]}/{tot[3]} ({_pct(tot[2], tot[3])})  {tot[4]}/{tot[5]} ({_pct(tot[4], tot[5])})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
