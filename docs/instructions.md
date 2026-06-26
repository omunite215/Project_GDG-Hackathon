# Instructions

How to set up, lint, test, and run RawLog Triage Pipeline. Commands are given for
PowerShell (the dev environment) and `make` (CI / Unix). Run them from the repo root.

## Prerequisites
- Python ≥3.12
- [Ollama](https://ollama.com) installed and running
- Pull the dev model **before the triage phase**:
  ```
  ollama pull gemma3:4b      # dev default
  ollama pull gemma3:12b     # quality pass (optional)
  ```

## Setup (create venv + install + install git hook)
PowerShell:
```
./scripts/setup.ps1
```
make:
```
make setup
```
This creates `.venv`, installs the project editable with dev extras
(`pip install -e .[dev]`), and points git at the committed hooks
(`git config core.hooksPath scripts/hooks`).

Activate the venv for ad-hoc commands:
```
.\.venv\Scripts\Activate.ps1      # PowerShell
```

## Lint & format
```
./scripts/lint.ps1     |   make lint     # ruff check . + ruff format --check .
ruff format .          |   make fmt      # auto-format
```
ruff must be clean before every commit — the pre-commit hook enforces this.

## Test
```
./scripts/test.ps1     |   make test     # pytest -q
```

## Run the pipeline
> Phase 0 prints a placeholder. Real ingest → triage → emit wiring lands in later phases.
```
./scripts/run.ps1 data/sample.log        |   make run
# or via the console script:
rawlog-triage data/sample.log
# or via stdin:
Get-Content data/sample.log | rawlog-triage
```

## Git / GitHub
The `origin` remote already exists
(`https://github.com/omunite215/Project_GDG-Hackathon.git`). Push each verified phase:
```
git add -A
git commit -m "Phase N: ..."
git push -u origin main
```
For reference, to create a fresh repo with the GitHub CLI (not installed here):
```
gh repo create Project_GDG-Hackathon --public --source . --remote origin --push
```
