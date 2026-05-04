.PHONY: help install lint format typecheck test check run

help:
	@echo "Targets: install lint format typecheck test check run"

install:
	python -m pip install -e ".[dev]"
	python -m pre_commit install

lint:
	python -m ruff check packages tests

format:
	python -m ruff format packages tests
	python -m ruff check --fix packages tests

typecheck:
	python -m mypy packages/devcd-core/src

test:
	python -m pytest tests -q

check: lint typecheck test

run:
	python -m devcd.cli serve --host 127.0.0.1 --port 8765
