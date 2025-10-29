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

## Testing the MCP Server

The MCP server can be tested both locally and after deployment.

### Local Testing

To test the MCP server locally:

1.  **Start the server:**

    ```bash
    export SEC_API_USER_AGENT="your.email@example.com"
    python main.py
    ```

    This will start the unified MCP server using stdio transport. You should see:
    
    ```
    🚀 DebtReversionAI MCP Server - Entry Point Wrapper
    Starting unified DebtReversionAI MCP server...
    Available tools: get_stock_data, calculate_macd, check_52week_low, check_optionable, search_debt_conversions, get_recent_filings
    ```

2.  **Test via Agent Integration:**

    The best way to test the server locally is through the agent:
    
    ```python
    from agents.dedalus_orchestrator import StockAnalysisAgent
    
    agent = StockAnalysisAgent()
    
    # List available tools
    tools = await agent.list_available_tools()
    print(tools)
    
    # Test a tool
    response = await agent.chat("Get stock data for AAPL")
    print(response)
    ```

### Deployed Testing

Once the server is deployed to Dedalus Labs as `ficonnectme2anymcp/DebtReversionAI`, test it through the agent:

```python
from agents.dedalus_orchestrator import StockAnalysisAgent

agent = StockAnalysisAgent()

# The agent connects to the deployed server
result = await agent.chat("Use stock ticker 'ATCH' and check the 52-week low")
print(result)
```

The agent's orchestrator (`agents/dedalus_orchestrator.py`) is configured to use:
```python
mcp_servers=["ficonnectme2anymcp/DebtReversionAI"]
```

This connects to your deployed unified MCP server and exposes all 6 tools to the LLM.
