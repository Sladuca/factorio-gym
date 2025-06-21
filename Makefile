# Factorio MCP Development Makefile

.PHONY: install dev-install format lint type-check test clean server

# Install dependencies
install:
	uv sync

# Install with dev dependencies
dev-install:
	uv sync --all-extras

# Format code
format:
	uv run black src/ scripts/ tests/
	uv run ruff format src/ scripts/ tests/

# Lint code
lint:
	uv run ruff check src/ scripts/ tests/

# Type check
type-check:
	uv run mypy src/ scripts/

# Run tests
test:
	uv run pytest

# Run all checks
check: lint type-check test

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Start development server
server:
	python3 scripts/dev_server.py

# Test RCON connection
test-rcon:
	python3 scripts/test_rcon.py --command "/help"

# Development help
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev-install - Install with dev dependencies"
	@echo "  format      - Format code with black and ruff"
	@echo "  lint        - Lint code with ruff"
	@echo "  type-check  - Type check with ty"
	@echo "  test        - Run tests"
	@echo "  check       - Run all checks (lint, type, test)"
	@echo "  clean       - Clean build artifacts"
	@echo "  server      - Start development server"
	@echo "  test-rcon   - Test RCON connection"
