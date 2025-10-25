# Testing Guide

This document outlines how to run the test suite for the DebtReversionAI project.

## Prerequisites

Before running the tests, ensure you have created the virtual environment and installed the necessary **development dependencies**.

```bash
# From the DebtReversionAI directory
# Ensure your virtual environment is activated
source aitinkerersdebtreversion/bin/activate

# Install development dependencies (includes pytest and ruff)
pip install -r requirements-dev.txt
```

## Running the Tests

The test suite uses the `pytest` framework. To run all the tests, navigate to the root of the `DebtReversionAI` directory and run the following command:

```bash
pytest
```

Pytest will automatically discover and run all the test files located in the `tests/` directory.

## Test Types

The test suite is composed of two main types of tests:

### 1. Unit Tests

The files `test_financial.py`, `test_edgar.py`, `test_dedalus.py`, and `test_manus.py` contain unit tests for the application's core components.

**Important:** These tests use mocking to isolate the code from external services. They **do not** make live network calls to `yfinance`, the SEC EDGAR API, Dedalus Labs, or Manus AI. This allows you to verify the internal logic of the application without needing API keys or a live internet connection.

### 2. Integration Tests

The file `test_integration.py` contains a placeholder for an end-to-end integration test. This test is currently **skipped** by default, as indicated by the `@pytest.mark.skip` decorator.

To run it, you would need a fully configured live environment, including:
- Valid API keys in your `.env` file.
- The MCP servers (`financial_server.py`, `edgar_server.py`) deployed on the Dedalus Labs platform.

This test is intended to verify the complete workflow of the agent interacting with all live services.
