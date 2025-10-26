"""
Unified MCP Server for DebtReversionAI
Combines financial data and EDGAR tools into a single server for Dedalus deployment
"""
import asyncio
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from servers.financial_server import FinancialDataServer
from servers.edgar_server import EdgarServer


class UnifiedDebtReversionServer:
    """Unified MCP server that routes tool calls to appropriate sub-servers"""
    
    def __init__(self, port=8000):
        self.server = Server("debt-reversion-ai", port=port)
        
        # Initialize sub-servers (without running them separately)
        self.financial_server = FinancialDataServer(port=None)
        self.edgar_server = EdgarServer(port=None)
        
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools from both financial and EDGAR servers"""
        
        @self.server.list_tools()
        async def list_tools():
            """Combine tools from both sub-servers"""
            financial_tools = [
                Tool(
                    name="get_stock_data",
                    description="Get stock price data including 52-week high/low",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "period": {"type": "string", "default": "1y"},
                        },
                        "required": ["ticker"],
                    },
                ),
                Tool(
                    name="calculate_macd",
                    description="Calculate MACD indicator for daily and weekly timeframes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "timeframe": {"type": "string", "enum": ["daily", "weekly"]},
                        },
                        "required": ["ticker", "timeframe"],
                    },
                ),
                Tool(
                    name="check_52week_low",
                    description="Check if stock is at or near 52-week low",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "tolerance": {"type": "number", "default": 0.05},
                        },
                        "required": ["ticker"],
                    },
                ),
                Tool(
                    name="check_optionable",
                    description="Verify if stock has options available",
                    inputSchema={
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"],
                    },
                ),
            ]
            
            edgar_tools = [
                Tool(
                    name="search_debt_conversions",
                    description="Search for debt conversion events in 8-K filings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "months_back": {"type": "integer", "default": 3},
                        },
                        "required": ["ticker"],
                    },
                ),
                Tool(
                    name="get_recent_filings",
                    description="Get recent SEC filings for a company",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "form_type": {"type": "string", "default": "8-K"},
                            "count": {"type": "integer", "default": 10},
                        },
                        "required": ["ticker"],
                    },
                ),
            ]
            
            return financial_tools + edgar_tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Route tool calls to the appropriate sub-server"""
            
            # Financial tools
            if name in ["get_stock_data", "calculate_macd", "check_52week_low", "check_optionable"]:
                if name == "get_stock_data":
                    return await self.financial_server._get_stock_data(
                        arguments["ticker"], arguments.get("period", "1y")
                    )
                elif name == "calculate_macd":
                    return await self.financial_server._calculate_macd(
                        arguments["ticker"], arguments["timeframe"]
                    )
                elif name == "check_52week_low":
                    return await self.financial_server._check_52week_low(
                        arguments["ticker"], arguments.get("tolerance", 0.05)
                    )
                elif name == "check_optionable":
                    return await self.financial_server._check_optionable(arguments["ticker"])
            
            # EDGAR tools
            elif name in ["search_debt_conversions", "get_recent_filings"]:
                if name == "search_debt_conversions":
                    return await self.edgar_server._search_debt_conversions(
                        arguments["ticker"], arguments.get("months_back", 3)
                    )
                elif name == "get_recent_filings":
                    return await self.edgar_server._get_recent_filings(
                        arguments["ticker"],
                        arguments.get("form_type", "8-K"),
                        arguments.get("count", 10)
                    )
            
            # Unknown tool
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """
    Main entrypoint for the unified MCP server.
    Dedalus Labs platform looks for this src/main.py file to start the server.
    """
    print("Starting unified DebtReversionAI MCP server...")

    # Set the SEC_API_USER_AGENT from environment variables for the Edgar functionality
    sec_identity = os.getenv("SEC_API_USER_AGENT")
    if not sec_identity:
        raise ValueError("SEC_API_USER_AGENT environment variable is not set. Please set it to a valid email address.")

    # Create and run the unified server
    unified_server = UnifiedDebtReversionServer(port=8000)
    
    print("Launching unified DebtReversionAI server on port 8000...")
    print("Available tools: get_stock_data, calculate_macd, check_52week_low, check_optionable, search_debt_conversions, get_recent_filings")
    
    await unified_server.server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server.")