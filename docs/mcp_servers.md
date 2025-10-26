# MCP Servers

This document provides an overview of the Model-Context-Protocol (MCP) servers used in the DebtReversionAI project. These servers provide specialized tools that can be called by agents to retrieve financial data and information from SEC filings.

## Overview

The MCP servers are built using the `mcp.server` library. They expose a set of tools that can be listed and called by an MCP client. Each server is responsible for a specific domain of data.

## Edgar Server

The Edgar Server (`mcp_servers/edgar_server.py`) interacts with the SEC's EDGAR database to retrieve information from company filings.

**Server Name:** `edgar-data`

### Tools

#### `search_debt_conversions`

Searches for debt conversion events in a company's 8-K filings.

*   **Description:** Search for debt conversion events in 8-K filings.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker of the company.
    *   `months_back` (integer, optional, default: 3): The number of months to look back for filings.
*   **Output:** A text summary of potential debt conversion events found, including filing dates, accession numbers, and extracted conversion prices.

#### `get_8k_filings`

Retrieves recent 8-K filings for a company.

*   **Description:** Get recent 8-K filings for a company.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker of the company.
    *   `limit` (integer, optional, default: 10): The maximum number of filings to return.
*   **Output:** A text summary of recent 8-K filings, including filing dates and URLs.

#### `extract_conversion_terms`

Extracts detailed debt conversion terms from a specific filing.

*   **Description:** Extract debt conversion terms from filing.
*   **Input Schema:**
    *   `filing_url` (string, required): The URL of the filing.
*   **Output:** A text summary of the extracted conversion terms. (Note: This is not fully implemented yet).

## Financial Data Server

The Financial Data Server (`mcp_servers/financial_server.py`) provides stock market data and technical indicators.

**Server Name:** `financial-data`

### Tools

#### `get_stock_data`

Retrieves stock price data, including 52-week high and low.

*   **Description:** Get stock price data including 52-week high/low.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `period` (string, optional, default: "1y"): The period over which to retrieve data (e.g., "1y", "6mo").
*   **Output:** A text summary of the stock data, including current price, 52-week high/low, and distance from high/low.

#### `calculate_macd`

Calculates the Moving Average Convergence Divergence (MACD) indicator for a stock.

*   **Description:** Calculate MACD indicator for daily and weekly timeframes.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `timeframe` (string, required, enum: ["daily", "weekly"]): The timeframe for the MACD calculation.
*   **Output:** A text summary of the MACD analysis, including the MACD line, signal line, histogram, and a bullish/bearish signal.

#### `check_52week_low`

Checks if a stock is at or near its 52-week low.

*   **Description:** Check if stock is at or near 52-week low.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
    *   `tolerance` (number, optional, default: 0.05): The percentage tolerance from the low (e.g., 0.05 for 5%).
*   **Output:** A text summary of the 52-week low analysis, including whether the stock is near its low within the given tolerance.

#### `check_optionable`

Verifies if a stock has options available for trading.

*   **Description:** Verify if stock has options available.
*   **Input Schema:**
    *   `ticker` (string, required): The stock ticker.
*   **Output:** A text summary indicating whether options are available, and if so, the number of expirations and the next expiration date.
