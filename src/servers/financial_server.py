from mcp.server import Server
from mcp.types import Tool, TextContent
import yfinance as yf
import pandas as pd
from datetime import datetime


class FinancialDataServer:
    def __init__(self, port=8000):
        # Only create server if port is specified (for standalone mode)
        if port is not None:
            self.server = Server("financial-data", port=port)
            self._register_tools()
        else:
            self.server = None

    def _register_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [
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
                            "timeframe": {
                                "type": "string",
                                "enum": ["daily", "weekly"],
                            },
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

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "get_stock_data":
                return await self._get_stock_data(
                    arguments["ticker"], arguments.get("period", "1y")
                )
            elif name == "calculate_macd":
                return await self._calculate_macd(
                    arguments["ticker"], arguments["timeframe"]
                )
            elif name == "check_52week_low":
                return await self._check_52week_low(
                    arguments["ticker"], arguments.get("tolerance", 0.05)
                )
            elif name == "check_optionable":
                return await self._check_optionable(arguments["ticker"])

    async def _get_stock_data(self, ticker: str, period: str):
        """Get stock data using yfinance"""
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return [
                TextContent(
                    type="text", text=f"Could not retrieve stock data for {ticker}."
                )
            ]

        current_price = hist["Close"].iloc[-1]
        week52_high = hist["High"].max()
        week52_low = hist["Low"].min()

        return [
            TextContent(
                type="text",
                text=f"""Stock Data for {ticker}:
- Current Price: ${current_price:.2f}
- 52-Week High: ${week52_high:.2f}
- 52-Week Low: ${week52_low:.2f}
- Distance from 52W Low: {((current_price - week52_low) / week52_low * 100):.2f}%
- Distance from 52W High: {((week52_high - current_price) / week52_high * 100):.2f}%
""",
            )
        ]

    def _calculate_macd_manual(self, close_prices: pd.Series):
        """
        Calculates MACD, Signal Line, and Histogram manually using pandas.
        """
        # Standard MACD parameters
        short_ema_period = 12
        long_ema_period = 26
        signal_ema_period = 9

        # Calculate the Short-term and Long-term Exponential Moving Averages (EMAs)
        short_ema = close_prices.ewm(span=short_ema_period, adjust=False).mean()
        long_ema = close_prices.ewm(span=long_ema_period, adjust=False).mean()

        # Calculate the MACD line
        macd_line = short_ema - long_ema

        # Calculate the Signal line
        signal_line = macd_line.ewm(span=signal_ema_period, adjust=False).mean()

        # Calculate the MACD Histogram
        histogram = macd_line - signal_line

        # Create a DataFrame to match the expected output format
        macd_df = pd.DataFrame({
            'MACD_12_26_9': macd_line,
            'MACDs_12_26_9': signal_line,
            'MACDh_12_26_9': histogram
        })

        return macd_df

    async def _calculate_macd(self, ticker: str, timeframe: str):
        """Calculate MACD indicator"""
        stock = yf.Ticker(ticker)

        if timeframe == "daily":
            hist = stock.history(period="6mo", interval="1d")
        else:  # weekly
            hist = stock.history(period="2y", interval="1wk")

        # Calculate MACD
        macd = self._calculate_macd_manual(hist["Close"])

        if macd is None or macd.empty:
            return [
                TextContent(
                    type="text", text=f"Could not calculate MACD for {ticker}."
                )
            ]

        current_price = hist["Close"].iloc[-1]
        macd_line = macd["MACD_12_26_9"].iloc[-1]
        signal_line = macd["MACDs_12_26_9"].iloc[-1]
        histogram = macd["MACDh_12_26_9"].iloc[-1]

        return [
            TextContent(
                type="text",
                text=f"""MACD Analysis for {ticker} ({timeframe}):
- Current Price: ${current_price:.2f}
- MACD Line: {macd_line:.4f}
- Signal Line: {signal_line:.4f}
- Histogram: {histogram:.4f}
- MACD Position: {"Below" if macd_line < 0 else "Above"} zero
- Signal: {"Bullish" if histogram > 0 else "Bearish"} crossover
- Price vs MACD: {"Above" if current_price > abs(macd_line) else "Below"} MACD level
""",
            )
        ]

    async def _check_52week_low(self, ticker: str, tolerance: float):
        """Check if stock is near 52-week low"""
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            return [
                TextContent(
                    type="text", text=f"Could not retrieve stock data for {ticker}."
                )
            ]

        current_price = hist["Close"].iloc[-1]
        week52_low = hist["Low"].min()
        week52_low_date = hist["Low"].idxmin()

        distance_pct = (current_price - week52_low) / week52_low
        is_near_low = distance_pct <= tolerance

        return [
            TextContent(
                type="text",
                text=f"""52-Week Low Analysis for {ticker}:
- Current Price: ${current_price:.2f}
- 52-Week Low: ${week52_low:.2f}
- 52W Low Date: {week52_low_date.strftime("%Y-%m-%d")}
- Distance: {distance_pct * 100:.2f}%
- Near 52W Low: {"✓ YES" if is_near_low else "✗ NO"} (tolerance: {tolerance * 100}%)
- Days Since Low: {(datetime.now() - week52_low_date).days} days
""",
            )
        ]

    async def _check_optionable(self, ticker: str):
        """Check if options are available"""
        try:
            stock = yf.Ticker(ticker)
            options_dates = stock.options

            if len(options_dates) > 0:
                # Get first expiration to verify options exist
                first_exp = options_dates[0]
                calls = stock.option_chain(first_exp).calls

                return [
                    TextContent(
                        type="text",
                        text=f"""Options Availability for {ticker}:
- Options Available: ✓ YES
- Number of Expirations: {len(options_dates)}
- Next Expiration: {first_exp}
- Call Options Available: {len(calls)}
- Options are tradeable: ✓ CONFIRMED
""",
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Options Availability for {ticker}: ✗ NO OPTIONS AVAILABLE",
                    )
                ]
        except Exception as e:
            return [
                TextContent(
                    type="text", text=f"Error checking options for {ticker}: {str(e)}"
                )
            ]
