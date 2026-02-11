# Tests Directory

This directory contains testing utilities and scripts for the PAT system.

## Structure

- **integration/** - End-to-end integration tests
- **unit/** - Unit tests for individual components
- **scripts/** - Manual testing scripts

## Usage

### Integration Tests

```bash
# Quick system test
python3 tests/pat_quick_test.py

# Full demo with all services
python3 tests/pat_demo.py
```

### Audio/Microphone Tests

```bash
# Test microphone functionality
python3 tests/test_microphone.py

# Alternative microphone test
python3 tests/test_microphone_alt.py

# Simple audio test
python3 tests/simple_audio_test.py
```

### Dependencies

Some tests require additional dependencies:
```bash
# Install test-specific requirements
pip install -r tests/mic_requirements.txt
# or
pip install -r tests/mic_requirements_alt.txt
```

## Notes

- Integration tests require all services to be running (`docker-compose up -d`)
- Audio tests require microphone permissions
- Tests are designed for local development and debugging