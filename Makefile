.PHONY: venv install format lint type clean test run help

# Default target
help:
	@echo "Available targets:"
	@echo "  venv     - Create virtual environment and install dependencies"
	@echo "  install  - Install dependencies in current environment"
	@echo "  format   - Format code with ruff"
	@echo "  lint     - Lint code with ruff"
	@echo "  type     - Type check with mypy"
	@echo "  clean    - Clean up temporary files"
	@echo "  test     - Run example transcription (requires .env file)"
	@echo "  run      - Run transcriber on sample file (requires .env file)"

# Create virtual environment and install dependencies
venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install -r requirements.txt

# Install dependencies in current environment
install:
	pip install -U pip
	pip install -r requirements.txt

# Format code
format:
	ruff format .

# Lint code
lint:
	ruff check .

# Type check
type:
	mypy transcriber --strict

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf outputs/ temp/ 2>/dev/null || true

# Test with a sample file (you need to provide a sample file)
test:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Copy env.example to .env and configure it."; exit 1; fi
	@echo "Note: Place a sample audio/video file in the current directory to test"
	@echo "Example: python -m transcriber.cli sample.mp3 --verbose"

# Run transcriber (example command)
run:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Copy env.example to .env and configure it."; exit 1; fi
	python -m transcriber.cli --help
