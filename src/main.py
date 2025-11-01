"""
Unified MCP Server for DebtReversionAI
Combines financial data and EDGAR tools into a single server for Dedalus deployment
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from src.tools.financial_tools import (
    get_stock_data as tools_get_stock_data,
    calculate_macd as tools_calculate_macd,
    check_52week_low as tools_check_52week_low,
    check_optionable as tools_check_optionable,
    get_stock_data_range as tools_get_stock_data_range,
)
from src.tools.edgar_tools import (
    search_debt_conversions as tools_search_debt_conversions,
    get_recent_filings as tools_get_recent_filings,
    extract_conversion_terms as tools_extract_conversion_terms,
)
from src.tools.markdown_tools import render_structured_result as tools_render_structured_result

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from current directory as fallback
    load_dotenv()

# Check for SEC_API_USER_AGENT early
sec_identity = os.getenv("SEC_API_USER_AGENT")
if not sec_identity:
    raise ValueError("SEC_API_USER_AGENT environment variable is not set. Please set it to a valid email address.")

# Determine host/port from environment or CLI args (default 8080)
import sys
import socket

# Top-level defaults (may be overridden in main())
_env_port = os.environ.get('PORT')
try:
    _default_port = int(_env_port) if _env_port is not None else 8080
except Exception:
    _default_port = 8080

_env_host = os.environ.get('HOST', '0.0.0.0')

# We'll set resolved host/port in main() but provide an initial value so FastMCP can be constructed.
# Use 0 so the server will bind to an ephemeral port by default unless overridden.
port = _default_port
host = _env_host


# Create FastMCP instance (host/port may be updated at runtime in main())
mcp = FastMCP(
    name='DebtReversionAI',
    host=host,
    port=port,
    instructions="""This MCP server provides financial analysis tools for identifying mean reversion opportunities.

Available tools:
- get_stock_data(ticker, period): Get stock price data including 52-week high/low
- calculate_macd(ticker, timeframe): Calculate MACD indicator for daily/weekly timeframes  
- check_52week_low(ticker, tolerance): Check if stock is at or near 52-week low
- check_optionable(ticker): Verify if stock has options available
- search_debt_conversions(ticker, months_back): Search for debt conversion events in 8-K filings
- get_recent_filings(ticker, form_type, count): Get recent SEC filings for a company

This server combines financial market data (via yfinance) with SEC EDGAR filing analysis.""",
)

# Tool implementations have been moved to src/tools/ and are used here as internal helpers


@mcp.tool()
async def get_stock_data(ticker: str, period: str = "1y") -> str:
    """Get stock price data (internal helper from src.tools.financial_tools)."""
    return await tools_get_stock_data(ticker, period)


@mcp.tool()
async def get_stock_data_range(ticker: str, start: str, end: str) -> str:
    """Get stock data for an exact date range. Wrapper around src.tools.financial_tools.get_stock_data_range."""
    return await tools_get_stock_data_range(ticker, start, end)


@mcp.tool()
async def calculate_macd(ticker: str, timeframe: str) -> str:
    """Calculate MACD using internal financial tools."""
    return await tools_calculate_macd(ticker, timeframe)


@mcp.tool()
async def check_52week_low(ticker: str, tolerance: float = 0.05) -> str:
    """Check 52-week low using internal financial tools."""
    return await tools_check_52week_low(ticker, tolerance)


@mcp.tool()
async def check_optionable(ticker: str) -> str:
    """Check option availability using internal financial tools."""
    return await tools_check_optionable(ticker)


@mcp.tool()
async def search_debt_conversions(ticker: str, months_back: int = 3) -> str:
    """Search for debt conversion events using internal EDGAR tools."""
    return await tools_search_debt_conversions(ticker, months_back)


@mcp.tool()
async def get_recent_filings(ticker: str, form_type: str = "8-K", count: int = 10) -> str:
    """Get recent filings using internal EDGAR tools."""
    return await tools_get_recent_filings(ticker, form_type, count)


@mcp.tool()
async def convert_to_markdown(structured: dict, options: dict = None) -> dict:
    """Convert a structured retrieval result into markdown chunks or snippet.

    Calls into src.tools.markdown_tools.render_structured_result which returns
    a dict containing either {'mode':'snippet','markdown':...} or
    {'mode':'chunked','chunks':[...]}.
    """
    # Render and return the dict directly so LLM callers can inspect chunks
    try:
        return tools_render_structured_result(structured or {}, options or {})
    except Exception as e:
        return {'error': str(e)}


def main():
    """Main entry point for the MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DebtReversionAI MCP Server')
    parser.add_argument('--port', type=int, help='Port for HTTP transport')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for HTTP transport')
    parser.add_argument('--stdio', action='store_true', help='Force STDIO transport')
    parser.add_argument('--test', action='store_true', help='Test mode')
    args = parser.parse_args()
    
    if args.test:
        print('DebtReversionAI MCP Server loaded successfully')
        print('Tools available: get_stock_data, calculate_macd, check_52week_low, check_optionable, search_debt_conversions, get_recent_filings')
        return 0
    
    # Determine transport mode (stdio is default for Dedalus)
    # Resolve host
    resolved_host = args.host or os.environ.get('HOST') or _env_host

    # Resolve port: prefer CLI arg, then environment, else choose ephemeral port
    resolved_port = None
    if args.port is not None:
        resolved_port = int(args.port)
    else:
        env_port = os.environ.get('PORT')
        if env_port:
            try:
                resolved_port = int(env_port)
            except ValueError:
                resolved_port = None

    if not args.stdio and (resolved_port is not None):
        # HTTP transport on explicit port
        # Update mcp instance with resolved values
        mcp.host = resolved_host
        mcp.port = resolved_port
        print(f'Starting HTTP server on {mcp.host}:{mcp.port}')
        mcp.run(transport='streamable-http')
    elif not args.stdio and (resolved_port is None):
        # No explicit port provided: choose an ephemeral port and bind to discover it
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((resolved_host, 0))
        chosen_port = s.getsockname()[1]
        s.close()
        mcp.host = resolved_host
        mcp.port = chosen_port
        print(f'No port provided; selected ephemeral port {mcp.port} on host {mcp.host}')
        mcp.run(transport='streamable-http')
    else:
        # STDIO transport (default for MCP/Dedalus)
        print('Starting unified DebtReversionAI MCP server via stdio transport...')
        print('Available tools: get_stock_data, calculate_macd, check_52week_low, check_optionable, search_debt_conversions, get_recent_filings')
        mcp.run('stdio')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())