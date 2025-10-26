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

## Testing the MCP Servers

The MCP servers can be tested both locally and after deployment.

### Local Testing

To test the MCP servers locally, you can run them directly from the `src/main.py` entrypoint and use a tool like `curl` to send requests.

1.  **Start the servers:**

    ```bash
    python src/main.py
    ```

    This will start both servers, with the Edgar server on port 8000 and the Financial Data server on port 8001.

2.  **Test with `curl`:**

    You can call the `list_tools` endpoint on each server to see the available tools.

    **Edgar Server:**
    ```bash
    curl -X POST http://localhost:8000/list_tools
    ```

    **Financial Data Server:**
    ```bash
    curl -X POST http://localhost:8001/list_tools
    ```

    To call a specific tool, you can send a POST request to the `call_tool` endpoint.

    **Example: `get_stock_data` on the Financial Data Server**
    ```bash
    curl -X POST http://localhost:8001/call_tool -H "Content-Type: application/json" -d '{"name": "get_stock_data", "arguments": {"ticker": "AAPL"}}'
    ```

### Deployed Testing

Once the servers are deployed to Dedalus Labs, you can use the `dedalus` CLI to test them.

1.  **List deployed services:**

    ```bash
    dedalus services list
    ```

2.  **Call a tool on a deployed service:**

    ```bash
    dedalus services call financial-data get_stock_data '{"ticker": "AAPL"}'
    ```

This allows you to test the deployed servers in the same way you would test them locally.
