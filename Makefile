.PHONY: help install lint format typecheck test check smoke distribution run docs docs-serve

help:
	@echo "Targets: install lint format typecheck test check smoke distribution run docs docs-serve"

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

test:
	python -m pytest tests -q

check: lint typecheck test

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
