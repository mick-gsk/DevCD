.PHONY: help install lint format typecheck typecheck-fast test test-fast test-fast-parallel test-affected test-slow check check-dev smoke distribution run docs docs-serve

help:
	@echo "Targets: install lint format typecheck typecheck-fast test test-fast test-fast-parallel test-affected test-slow check check-dev smoke distribution run docs docs-serve"

install:
	python -m pip install -e ".[dev]"
	python -m pre_commit install

lint:
	python -m ruff check packages tests scripts

format:
	python -m ruff format packages tests scripts
	python -m ruff check --fix packages tests scripts

typecheck:
	python -m mypy packages/devcd-core/src

typecheck-fast:
	python -m mypy.dmypy run -- packages/devcd-core/src

test:
	python -m pytest tests -q

test-fast:
	python -m pytest tests -q -m "not slow"

test-fast-parallel:
	python -c "import importlib.util, subprocess, sys; has_xdist = importlib.util.find_spec('xdist') is not None; cmd = [sys.executable, '-m', 'pytest', 'tests', '-q', '-m', 'not slow']; cmd += ['-n', 'auto'] if has_xdist else []; print('Using pytest-xdist parallel mode.' if has_xdist else 'pytest-xdist not installed; falling back to serial test-fast.'); raise SystemExit(subprocess.call(cmd))"

test-affected:
	python -c "import importlib.util, subprocess, sys; has_testmon = importlib.util.find_spec('testmon') is not None; cmd = [sys.executable, '-m', 'pytest', 'tests', '-q', '-m', 'not slow']; cmd += ['--testmon'] if has_testmon else []; print('Using pytest-testmon affected-test mode.' if has_testmon else 'pytest-testmon not installed; falling back to test-fast.'); raise SystemExit(subprocess.call(cmd))"

test-slow:
	python -m pytest tests -q -m "slow"

check: lint typecheck test

check-dev: lint typecheck-fast test-affected

smoke:
	python scripts/smoke_cli.py

distribution:
	python -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"
	python -m build
	python -m twine check dist/*
	python scripts/check_distribution.py

run:
	python -m devcd.cli serve --host 127.0.0.1 --port 8765

docs:
	mkdocs build --strict

docs-serve:
	mkdocs serve
