# Variables
UV           := uv
MAIN         := pac-man.py
CONFIG       := config.json
SRC_DIR      := pacman
ALL_PY       := $(MAIN) $(SRC_DIR)

.PHONY: all install run debug clean lint lint-strict

all: run

# Install/sync dependencies and virtual environment using uv
install:
	$(UV) sync

# Run the game using uv run
run:
	$(UV) run python $(MAIN) $(CONFIG)

# Debug mode with Python's pdb inside uv environment
debug:
	$(UV) run python -m pdb $(MAIN) $(CONFIG)

# Remove build artifacts, pycache, and uv environment if needed
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Mandatory lint rule via uv run with exact subject flags
lint:
	$(UV) run flake8 $(ALL_PY)
	$(UV) run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	         --disallow-untyped-defs --check-untyped-defs $(ALL_PY)

# Optional strict lint rule
lint-strict:
	$(UV) run flake8 $(ALL_PY)
	$(UV) run mypy --strict $(ALL_PY)