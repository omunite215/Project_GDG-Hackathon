.PHONY: setup lint fmt test run hook

# Create venv, install editable + dev, install git hook.
setup:
	python -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"
	git config core.hooksPath scripts/hooks

# Lint + format check (mirrors the pre-commit hook).
lint:
	ruff check .
	ruff format --check .

# Auto-format.
fmt:
	ruff format .

# Run tests.
test:
	pytest

# Run the pipeline (pass a log file): make run ARGS=data/sample.log
run:
	rawlog-triage $(ARGS)

# Install the git hook only.
hook:
	git config core.hooksPath scripts/hooks
