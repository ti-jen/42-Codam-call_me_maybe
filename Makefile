PYTHON = python3
VENV = .venv
MAIN = main.py

.PHONY: install run debug clean lint lint-strict

run:
	$(PYTHON) $(MAIN) $(MAP)

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .venv

lint:
	uv run flake8 --exclude=.venv,llm_sdk
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 --exclude=.venv,llm_sdk
	uv run mypy . --strict
