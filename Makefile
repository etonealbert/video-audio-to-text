# Cross-platform Makefile for transcriber project
# Supports Unix/macOS/Linux (default) and Windows (with GNU Make or make.exe)

.PHONY: venv install format lint type clean test run help setup-env check-env detect-os

# OS Detection
ifeq ($(OS),Windows_NT)
	DETECTED_OS := Windows
	PYTHON := python
	VENV_DIR := .venv
	VENV_ACTIVATE := $(VENV_DIR)\Scripts\activate.bat
	VENV_PYTHON := $(VENV_DIR)\Scripts\python.exe
	VENV_PIP := $(VENV_DIR)\Scripts\pip.exe
	RM := del /q
	RM_RF := rmdir /s /q
	MKDIR := mkdir
	SHELL_CMD := cmd /c
	PATH_SEP := \\
	NULL_REDIRECT := >nul 2>&1
else
	DETECTED_OS := Unix
	PYTHON := python3
	VENV_DIR := .venv
	VENV_ACTIVATE := $(VENV_DIR)/bin/activate
	VENV_PYTHON := $(VENV_DIR)/bin/python
	VENV_PIP := $(VENV_DIR)/bin/pip
	RM := rm -f
	RM_RF := rm -rf
	MKDIR := mkdir -p
	SHELL_CMD := 
	PATH_SEP := /
	NULL_REDIRECT := >/dev/null 2>&1
endif

# Default target
help:
	@echo "Cross-platform Makefile for transcriber (Detected OS: $(DETECTED_OS))"
	@echo ""
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  detect-os   - Show detected operating system"
	@echo "  venv        - Create virtual environment and install dependencies"
	@echo "  install     - Install dependencies in current environment"
	@echo "  setup-env   - Setup .env file from template"
	@echo "  format      - Format code with ruff"
	@echo "  lint        - Lint code with ruff"
	@echo "  type        - Type check with mypy"
	@echo "  clean       - Clean up temporary files"
	@echo "  test        - Run example transcription (requires .env file)"
	@echo "  run         - Run transcriber help (requires .env file)"
	@echo "  check-env   - Check if .env file exists"
	@echo ""
	@echo "Cross-platform commands:"
	@echo "  make venv        # Create virtual environment"
	@echo "  make install     # Install dependencies"
	@echo "  make setup-env   # Copy env.example to .env"
	@echo "  make format      # Format code"
	@echo "  make clean       # Clean temp files"

# Detect and display OS
detect-os:
	@echo "Detected operating system: $(DETECTED_OS)"
	@echo "Python command: $(PYTHON)"
	@echo "Virtual environment directory: $(VENV_DIR)"
	@echo "Path separator: $(PATH_SEP)"

# Create virtual environment and install dependencies
venv:
	@echo "Creating virtual environment for $(DETECTED_OS)..."
ifeq ($(DETECTED_OS),Windows)
	$(PYTHON) -m venv $(VENV_DIR)
	$(SHELL_CMD) "$(VENV_PIP) install -U pip"
	$(SHELL_CMD) "$(VENV_PIP) install -r requirements.txt"
	@echo ""
	@echo "Virtual environment created successfully!"
	@echo "To activate on Windows, run: $(VENV_DIR)\\Scripts\\Activate.ps1"
	@echo "Or in CMD: $(VENV_DIR)\\Scripts\\activate.bat"
else
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_ACTIVATE) && pip install -U pip
	. $(VENV_ACTIVATE) && pip install -r requirements.txt
	@echo ""
	@echo "Virtual environment created successfully!"
	@echo "To activate on Unix/macOS, run: source $(VENV_ACTIVATE)"
endif

# Install dependencies in current environment
install:
	@echo "Installing dependencies for $(DETECTED_OS)..."
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -r requirements.txt

# Setup environment file
setup-env:
	@echo "Setting up .env file..."
ifeq ($(DETECTED_OS),Windows)
	@if not exist .env (copy env.example .env && echo .env file created from template) else (echo .env file already exists)
else
	@if [ ! -f .env ]; then cp env.example .env && echo ".env file created from template"; else echo ".env file already exists"; fi
endif

# Check if .env file exists
check-env:
ifeq ($(DETECTED_OS),Windows)
	@if exist .env (echo .env file found) else (echo ERROR: .env file not found. Run 'make setup-env' to create it.)
else
	@if [ -f .env ]; then echo ".env file found"; else echo "ERROR: .env file not found. Run 'make setup-env' to create it."; fi
endif

# Format code
format:
	@echo "Formatting code..."
	$(PYTHON) -m ruff format .

# Lint code
lint:
	@echo "Linting code..."
	$(PYTHON) -m ruff check .

# Type check
type:
	@echo "Type checking..."
	$(PYTHON) -m mypy transcriber --strict

# Clean up temporary files
clean:
	@echo "Cleaning temporary files for $(DETECTED_OS)..."
ifeq ($(DETECTED_OS),Windows)
	@if exist __pycache__ $(RM_RF) __pycache__ $(NULL_REDIRECT)
	@if exist .mypy_cache $(RM_RF) .mypy_cache $(NULL_REDIRECT)
	@if exist .ruff_cache $(RM_RF) .ruff_cache $(NULL_REDIRECT)
	@if exist transcriber\\__pycache__ $(RM_RF) transcriber\\__pycache__ $(NULL_REDIRECT)
	@if exist outputs $(RM_RF) outputs $(NULL_REDIRECT)
	@if exist temp $(RM_RF) temp $(NULL_REDIRECT)
	@for /r %%i in (*.pyc) do @$(RM) "%%i" $(NULL_REDIRECT)
	@echo Cleanup completed.
else
	@find . -type d -name "__pycache__" -exec rm -rf {} + $(NULL_REDIRECT) || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + $(NULL_REDIRECT) || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + $(NULL_REDIRECT) || true
	@find . -name "*.pyc" -delete $(NULL_REDIRECT) || true
	@$(RM_RF) outputs/ temp/ $(NULL_REDIRECT) || true
	@echo "Cleanup completed."
endif

# Test with a sample file
test: check-env
	@echo "Running test..."
	@echo "Note: Place a sample audio/video file in the current directory to test"
	@echo "Example: $(PYTHON) -m transcriber.cli sample.mp3 --verbose"

# Run transcriber help
run: check-env
	@echo "Running transcriber..."
	$(PYTHON) -m transcriber.cli --help
