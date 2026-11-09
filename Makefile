PYTHON = python3
VENV = .venv
MAIN = src

.PHONY: install run debug clean lint lint-strict

install:
	uv sync

run:
	uv run $(PYTHON) -m $(MAIN)

debug:
	uv run $(PYTHON) -m  pdb -m $(MAIN)

test:
	uv run $(PYTHON) -m $(MAIN) --functions_definition moulinette/data/input/functions_definition.json --input moulinette/data/input/function_calling_tests.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .venv

lint:
	uv run flake8 --exclude=.venv,llm_sdk,moulinette
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 --exclude=.venv,llm_sdk,moulinette
	uv run mypy . --strict
