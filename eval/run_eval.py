"""Golden-set evaluation for triage().

Runs the real `triage()` over `eval/golden.jsonl` and reports the three demo numbers:
JSON-valid %, detection accuracy %, and severity accuracy %.

Run (needs Ollama running with the model pulled):
    python eval/run_eval.py [--model gemma3:4b] [--golden eval/golden.jsonl]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rawlog_triage.schema import TriageResult
from rawlog_triage.triage import triage


def load_cases(path: str) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _is_valid(result: TriageResult | None) -> bool:
    # Valid = a clean no-incident (None) or a real result that isn't the unparseable sentinel.
    if result is None:
        return True
    return result.service_name != "unparseable"


def _pct(num: int, denom: int) -> str:
    return f"{100 * num / denom:.0f}%" if denom else "n/a"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_eval")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--golden", default=str(Path(__file__).with_name("golden.jsonl")))
    args = parser.parse_args(argv)

    cases = load_cases(args.golden)
    results = [triage(case["chunk"], model=args.model) for case in cases]

    valid = detect_ok = sev_ok = sev_total = 0
    print(f"{'case':<26}{'expected':<10}{'predicted':<13}{'valid':<7}{'detect':<8}sev")
    print("-" * 72)
    for case, result in zip(cases, results, strict=True):
        expected = case["expected_severity"] if case["expect_incident"] else "None"
        if result is None:
            predicted = "None"
        elif result.service_name == "unparseable":
            predicted = "UNPARSEABLE"
        else:
            predicted = result.error_severity

        is_valid = _is_valid(result)
        detected = (result is not None) == case["expect_incident"]
        valid += is_valid
        detect_ok += detected

        if case["expect_incident"]:
            sev_total += 1
            severity_ok = (
                isinstance(result, TriageResult)
                and result.service_name != "unparseable"
                and result.error_severity == case["expected_severity"]
            )
            sev_ok += severity_ok
            sev_mark = "OK" if severity_ok else "X"
        else:
            sev_mark = "-"

        print(
            f"{case['name']:<26}{expected:<10}{predicted:<13}"
            f"{('OK' if is_valid else 'X'):<7}{('OK' if detected else 'X'):<8}{sev_mark}"
        )

    n = len(cases)
    print("-" * 72)
    print(f"model: {args.model}   cases: {n}")
    print(f"JSON-valid:  {valid}/{n} ({_pct(valid, n)})")
    print(f"detection:   {detect_ok}/{n} ({_pct(detect_ok, n)})")
    print(f"severity:    {sev_ok}/{sev_total} ({_pct(sev_ok, sev_total)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
