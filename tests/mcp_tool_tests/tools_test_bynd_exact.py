#!/usr/bin/env python3
"""Test script: exact-date fetch for BYND and HTTP attempt against MCP server.

This copy lives under tests/mcp_tool_tests for archival/debug runs.
"""
import json
import sys
import time
from datetime import datetime

try:
    import yfinance as yf
except Exception as e:
    print("Missing dependency yfinance:", e)
    sys.exit(2)

from urllib import request


def format_stock_summary(ticker: str, hist):
    if hist.empty:
        return f"Could not retrieve stock data for {ticker}."

    current_price = hist['Close'].iloc[-1]
    week52_high = hist['High'].max()
    week52_low = hist['Low'].min()

    return (
        f"Stock Data for {ticker}:\n"
        f"- Current Price: ${current_price:.2f}\n"
        f"- 52-Week High: ${week52_high:.2f}\n"
        f"- 52-Week Low: ${week52_low:.2f}\n"
        f"- Distance from 52W Low: {((current_price - week52_low) / week52_low * 100):.2f}%\n"
        f"- Distance from 52W High: {((week52_high - current_price) / week52_high * 100):.2f}%\n"
    )


def simulate_exact_range(ticker: str, start: str, end: str):
    print(f"Simulating exact date-range fetch for {ticker}: {start} -> {end}")
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)
    print(format_stock_summary(ticker, hist))


def attempt_http_call(ticker: str, start: str, end: str, host='127.0.0.1', port=39775):
    url = f'http://{host}:{port}/mcp'
    print(f"Attempting HTTP POST to {url} (best-effort payload)...")

    payload = {
        "jsonrpc": "2.0",
        "method": "call_tool",
        "params": {
            "tool": "get_stock_data",
            "args": {"ticker": ticker, "start": start, "end": end},
        },
        "id": 1,
    }

    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode('utf-8')
            print('HTTP response status:', resp.status)
            print('HTTP response body:')
            print(body)
    except Exception as e:
        print('HTTP request failed:', repr(e))


if __name__ == '__main__':
    ticker = 'BYND'
    start = '2025-10-13'
    end = '2025-10-18'

    simulate_exact_range(ticker, start, end)

    print('\nNow attempting HTTP call to a running MCP on port 39775...')
    attempt_http_call(ticker, start, end)
