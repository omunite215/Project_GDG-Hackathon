"""Download the LogHub 2k structured CSVs used by the eval harness.

Pulls `<System>_2k.log_structured.csv` for each dataset from the public logpai/loghub repo
into `eval/loghub/` (gitignored). Run once before `build_golden.py`:

    python eval/fetch_loghub.py
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/logpai/loghub/master"

# folder -> dataset stem (the structured CSV is "<stem>_2k.log_structured.csv")
DATASETS = {
    "HDFS": "HDFS",
    "Hadoop": "Hadoop",
    "Spark": "Spark",
    "Zookeeper": "Zookeeper",
    "OpenStack": "OpenStack",
    "BGL": "BGL",
    "HPC": "HPC",
    "Thunderbird": "Thunderbird",
    "Windows": "Windows",
    "Linux": "Linux",
    "Mac": "Mac",
    "Android": "Android",
    "Apache": "Apache",
    "OpenSSH": "OpenSSH",
    "Proxifier": "Proxifier",
    "HealthApp": "HealthApp",
}

OUT = Path(__file__).with_name("loghub")
# Spec-mandated raw sample (HDFS, fallback Linux) committed to data/ for the demo.
SAMPLE_DEST = Path(__file__).resolve().parents[1] / "data" / "sample_production_logs.txt"
SAMPLE_SOURCES = [f"{RAW}/HDFS/HDFS_2k.log", f"{RAW}/Linux/Linux_2k.log"]


def _fetch_sample() -> None:
    if SAMPLE_DEST.exists() and SAMPLE_DEST.stat().st_size > 0:
        print(f"  cached  {SAMPLE_DEST.name}")
        return
    for url in SAMPLE_SOURCES:
        try:
            urllib.request.urlretrieve(url, SAMPLE_DEST)  # noqa: S310 (trusted github raw URL)
            print(f"  fetched {SAMPLE_DEST.name} from {url} ({SAMPLE_DEST.stat().st_size:,} bytes)")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED  {url}: {exc}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    for folder, stem in DATASETS.items():
        name = f"{stem}_2k.log_structured.csv"
        dest = OUT / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  cached  {folder}/{name}")
            ok += 1
            continue
        url = f"{RAW}/{folder}/{name}"
        try:
            urllib.request.urlretrieve(url, dest)  # noqa: S310 (trusted github raw URL)
            print(f"  fetched {folder}/{name} ({dest.stat().st_size:,} bytes)")
            ok += 1
        except Exception as exc:  # noqa: BLE001  (network / 404)
            print(f"  FAILED  {folder}/{name}: {exc}")
    print(f"\n{ok}/{len(DATASETS)} datasets available in {OUT}")
    print("\nRaw demo sample:")
    _fetch_sample()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
