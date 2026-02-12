# PAT Backend Tests

This directory contains all tests for the PAT backend application.

## Structure

- `integration/` - Integration tests that test multiple components/services together
  - `email_ai_test.py` - Tests for email AI functionality
  - `direct_sync_test.py` - Tests for direct synchronization
  - `icloud_sync_test.py` - Tests for iCloud synchronization
  - `single_sync_test.py` - Tests for single-item synchronization
  - `task_sync_test.py` - Tests for task synchronization
- `unit/` - Unit tests for individual functions and classes
- `performance testing/` - Performance and load testing

## Running Tests

```bash
# Run all tests
pytest

# Run integration tests only
pytest tests/integration/

# Run specific test file
pytest tests/integration/email_ai_test.py

# Run with coverage
pytest --cov=src --cov-report=html
```

## Adding New Tests

1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Place performance tests in `tests/performance testing/`
4. Follow the naming convention `test_<module>_<feature>.py`