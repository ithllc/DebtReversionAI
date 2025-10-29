# MCP Servers

This document provides an overview of the Model-Context-Protocol (MCP) servers used in the DebtReversionAI project. These servers provide specialized tools that can be called by agents to retrieve financial data and information from SEC filings.

## Overview

The MCP servers are built using the `mcp.server` library. They expose a set of tools that can be listed and called by an MCP client.

**Architecture**: As of the latest update, the project uses a **unified MCP server** architecture where a single server (`debt-reversion-ai`) combines tools from multiple domains (financial data and SEC filings) and routes calls to the appropriate implementation.

## Unified Server Architecture

### How it Works

The DebtReversionAI MCP server uses a **tool routing pattern** to combine multiple specialized servers into a single unified endpoint:

```
ficonnectme2anymcp/DebtReversionAI (Deployed Server)
    ↓
UnifiedDebtReversionServer (Main Entry Point)
    ↓
Tool Router (routes based on tool name)
    ├─→ FinancialDataServer (stock data, MACD, options)
    └─→ EdgarServer (SEC filings, debt conversions)
```

**Key Components:**

1.  **UnifiedDebtReversionServer** (`src/main.py`): 
    - Single entry point that Dedalus platform recognizes
    - Combines tool definitions from both financial and EDGAR domains
    - Routes tool calls to appropriate sub-server implementation

2.  **FinancialDataServer** (`src/servers/financial_server.py`):
    - Provides stock market data and technical indicators
    - Used as a sub-component (no independent server)

3.  **EdgarServer** (`src/servers/edgar_server.py`):
    - Provides SEC EDGAR filing data and analysis
    - Used as a sub-component (no independent server)

### Deployment

When deployed to Dedalus Labs, the unified server:
- Uses **stdio transport** (stdin/stdout) for Model Context Protocol communication
- Entry point: `main.py` (wrapper) → `src/main.py` (actual server)
- Is accessible as: `ficonnectme2anymcp/DebtReversionAI`
- Exposes **all tools** from both financial and EDGAR servers through a single endpoint
- Requires environment variable: `SEC_API_USER_AGENT` (your email address)

### Deployment Architecture

The project uses an **entry point wrapper pattern**:

```
Dedalus runs: uv run main
    ↓
main.py (wrapper with error handling)
    ↓
imports src.main and runs server_main()
    ↓
src/main.py: UnifiedDebtReversionServer
    ↓
stdio_server() context manager
    ↓
server.run(read_stream, write_stream, init_options)
```

This pattern ensures:
- MCP server (not agent) starts when deployed
- Comprehensive error handling and debugging output
- Proper stdio transport for MCP communication

### Agent Integration

The orchestrator (`agents/dedalus_orchestrator.py`) connects to the MCP server:

```python
result = await self.runner.run(
    input=user_message,
    model="anthropic/claude-sonnet-4-20250514",
    mcp_servers=["ficonnectme2anymcp/DebtReversionAI"],  # Single unified server
    instructions=SYSTEM_PROMPT,
    stream=False,
)
```

The LLM receives **all 6 tools** and can call any of them as needed for the analysis workflow.

---

## Available Tools

The unified server exposes the following tools:

---

## Available Tools

The unified server exposes the following tools:

### Financial Data Tools (from FinancialDataServer)

#### `get_stock_data`

Retrieves stock price data, including 52-week high and low.

*   **Description:** Get stock price data including 52-week high/low.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `period` (string, optional, default: "1y"): The period over which to retrieve data (e.g., "1y", "6mo").
*   **Output:** A text summary of the stock data, including current price, 52-week high/low, and distance from high/low.
*   **Implementation:** Routes to `FinancialDataServer._get_stock_data()`

#### `calculate_macd`

Calculates the Moving Average Convergence Divergence (MACD) indicator for a stock.

*   **Description:** Calculate MACD indicator for daily and weekly timeframes.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `timeframe` (string, required, enum: ["daily", "weekly"]): The timeframe for the MACD calculation.
*   **Output:** A text summary of the MACD analysis, including the MACD line, signal line, histogram, and a bullish/bearish signal.
*   **Implementation:** Routes to `FinancialDataServer._calculate_macd()`

#### `check_52week_low`

Checks if a stock is at or near its 52-week low.

*   **Description:** Check if stock is at or near 52-week low.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `tolerance` (number, optional, default: 0.05): The percentage tolerance from the low (e.g., 0.05 for 5%).
*   **Output:** A text summary of the 52-week low analysis, including whether the stock is near its low within the given tolerance.
*   **Implementation:** Routes to `FinancialDataServer._check_52week_low()`

#### `check_optionable`

Verifies if a stock has options available for trading.

*   **Description:** Verify if stock has options available.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
*   **Output:** A text summary indicating whether options are available, and if so, the number of expirations and the next expiration date.
*   **Implementation:** Routes to `FinancialDataServer._check_optionable()`

---

### SEC Filing Tools (from EdgarServer)

#### `search_debt_conversions`

Searches for debt conversion events in a company's 8-K filings.

*   **Description:** Search for debt conversion events in 8-K filings.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker of the company.
    *   `months_back` (integer, optional, default: 3): The number of months to look back for filings.
*   **Output:** A text summary of potential debt conversion events found, including filing dates, accession numbers, and extracted conversion prices.
*   **Implementation:** Routes to `EdgarServer._search_debt_conversions()`

#### `get_recent_filings`

Retrieves recent SEC filings for a company.

*   **Description:** Get recent SEC filings for a company.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker of the company.
    *   `form_type` (string, optional, default: "8-K"): The type of filing to retrieve.
    *   `count` (integer, optional, default: 10): The maximum number of filings to return.
*   **Output:** A text summary of recent filings, including filing dates and URLs.
*   **Implementation:** Routes to `EdgarServer._get_recent_filings()`

---

## Tool Routing Logic

The `UnifiedDebtReversionServer.call_tool()` method handles routing:

```python
async def call_tool(name: str, arguments: dict):
    """Route tool calls to the appropriate sub-server"""
    
    # Financial tools
    if name in ["get_stock_data", "calculate_macd", "check_52week_low", "check_optionable"]:
        # Route to FinancialDataServer
        return await self.financial_server._method_name(...)
    
    # EDGAR tools
    elif name in ["search_debt_conversions", "get_recent_filings"]:
        # Route to EdgarServer
        return await self.edgar_server._method_name(...)
```

This routing happens transparently to the LLM - it simply calls the tool by name and receives the result.

---

## Testing MCP Server

### List Available Tools

Use the orchestrator's `list_available_tools()` method:

```python
from agents.dedalus_orchestrator import StockAnalysisAgent

agent = StockAnalysisAgent()
tools = await agent.list_available_tools()
print(tools)
```

**Expected output**: List of all 6 tools (4 financial + 2 EDGAR)

### Test Tool Calls

```python
# Test financial tool
response = await agent.chat("Get stock data for AAPL")

# Test EDGAR tool  
response = await agent.chat("Search for debt conversions in TSLA filings")
```

---

## Migration Notes

**Previous Architecture** (deprecated):
- Two separate servers: `financial-data` (port 8000) and `edgar-data` (port 8001)
- Required Dedalus to merge tools from multiple endpoints
- Tools were not consistently accessible to the LLM

**Current Architecture** (recommended):
- Single unified server: `debt-reversion-ai` (stdio transport)
- Entry point wrapper: `main.py` → `src/main.py`
- All tools registered and routed through one entry point
- Guaranteed tool accessibility to the LLM
- Simpler deployment and debugging
- Requires: `SEC_API_USER_AGENT` environment variable

**Local Testing Only**:
For local development, you can run the server directly:

```bash
export SEC_API_USER_AGENT="your.email@example.com"
python main.py
```

The server will start with stdio transport and wait for MCP protocol messages on stdin.
