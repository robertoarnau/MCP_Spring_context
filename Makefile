.PHONY: help test test-verbose test-coverage test-unit test-integration install clean

# Default target
help:
	@echo "Available commands:"
	@echo "  test          - Run all tests"
	@echo "  test-verbose  - Run tests with verbose output"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  test-unit     - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  install       - Install test dependencies"
	@echo "  clean         - Clean up test artifacts"

# Install test dependencies
install:
	pip install -r requirements.txt
	pip install pytest-cov

# Run all tests
test:
	pytest

# Run tests with verbose output
test-verbose:
	pytest -v

# Run tests with coverage
test-coverage:
	pytest --cov=mcp_server --cov-report=html --cov-report=term-missing

# Run only unit tests
test-unit:
	pytest -m "not integration"

# Run only integration tests
test-integration:
	pytest -m integration

# Clean up test artifacts
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=test_file.py"; \
		exit 1; \
	fi
	pytest tests/$(FILE)

# Run tests with pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_function"; \
		exit 1; \
	fi
	pytest -k $(PATTERN)
