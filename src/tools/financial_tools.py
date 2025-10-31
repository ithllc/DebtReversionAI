from mcp.types import TextContent
import yfinance as yf
import pandas as pd
from datetime import datetime


async def get_stock_data(ticker: str, period: str = "1y") -> str:
    """Get stock data using yfinance and return a textual summary"""
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    if hist.empty:
        return f"Could not retrieve stock data for {ticker}."

    current_price = hist["Close"].iloc[-1]
    week52_high = hist["High"].max()
    week52_low = hist["Low"].min()

    return (
        f"""Stock Data for {ticker}:
- Current Price: ${current_price:.2f}
- 52-Week High: ${week52_high:.2f}
- 52-Week Low: ${week52_low:.2f}
- Distance from 52W Low: {((current_price - week52_low) / week52_low * 100):.2f}%
- Distance from 52W High: {((week52_high - current_price) / week52_high * 100):.2f}%
"""
    )


async def get_stock_data_range(ticker: str, start: str, end: str) -> str:
    """Get stock data for an exact date range (start inclusive, end exclusive)."""
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)

    if hist.empty:
        return f"Could not retrieve stock data for {ticker} in range {start} -> {end}."

    current_price = hist["Close"].iloc[-1]
    week52_high = hist["High"].max()
    week52_low = hist["Low"].min()

    return (
        f"""Stock Data for {ticker} ({start} -> {end}):
- Current Price: ${current_price:.2f}
- 52-Week High: ${week52_high:.2f}
- 52-Week Low: ${week52_low:.2f}
- Distance from 52W Low: {((current_price - week52_low) / week52_low * 100):.2f}%
- Distance from 52W High: {((week52_high - current_price) / week52_high * 100):.2f}%
"""
    )


def _calculate_macd_manual(close_prices: pd.Series) -> pd.DataFrame:
    """
    Calculates MACD, Signal Line, and Histogram manually using pandas.
    """
    short_ema_period = 12
    long_ema_period = 26
    signal_ema_period = 9

    short_ema = close_prices.ewm(span=short_ema_period, adjust=False).mean()
    long_ema = close_prices.ewm(span=long_ema_period, adjust=False).mean()

    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_ema_period, adjust=False).mean()
    histogram = macd_line - signal_line

    macd_df = pd.DataFrame({
        'MACD_12_26_9': macd_line,
        'MACDs_12_26_9': signal_line,
        'MACDh_12_26_9': histogram,
    })

    return macd_df


async def calculate_macd(ticker: str, timeframe: str) -> str:
    stock = yf.Ticker(ticker)

    if timeframe == "daily":
        hist = stock.history(period="6mo", interval="1d")
    else:
        hist = stock.history(period="2y", interval="1wk")

    if hist.empty:
        return f"Could not calculate MACD for {ticker}."

    macd = _calculate_macd_manual(hist["Close"])

    if macd is None or macd.empty:
        return f"Could not calculate MACD for {ticker}."

    current_price = hist["Close"].iloc[-1]
    macd_line = macd["MACD_12_26_9"].iloc[-1]
    signal_line = macd["MACDs_12_26_9"].iloc[-1]
    histogram = macd["MACDh_12_26_9"].iloc[-1]

    return (
        f"""MACD Analysis for {ticker} ({timeframe}):
- Current Price: ${current_price:.2f}
- MACD Line: {macd_line:.4f}
- Signal Line: {signal_line:.4f}
- Histogram: {histogram:.4f}
- MACD Position: {"Below" if macd_line < 0 else "Above"} zero
- Signal: {"Bullish" if histogram > 0 else "Bearish"} crossover
- Price vs MACD: {"Above" if current_price > abs(macd_line) else "Below"} MACD level
"""
    )


async def check_52week_low(ticker: str, tolerance: float) -> str:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    if hist.empty:
        return f"Could not retrieve stock data for {ticker}."

    current_price = hist["Close"].iloc[-1]
    week52_low = hist["Low"].min()
    week52_low_date = hist["Low"].idxmin()

    distance_pct = (current_price - week52_low) / week52_low
    is_near_low = distance_pct <= tolerance

    return (
        f"""52-Week Low Analysis for {ticker}:
- Current Price: ${current_price:.2f}
- 52-Week Low: ${week52_low:.2f}
- 52W Low Date: {week52_low_date.strftime("%Y-%m-%d")}
- Distance: {distance_pct * 100:.2f}%
- Near 52W Low: {{}} (tolerance: {tolerance * 100}%)
- Days Since Low: { (datetime.now() - week52_low_date).days } days
""".format("✓ YES" if is_near_low else "✗ NO")
    )


async def check_optionable(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        options_dates = stock.options

        if len(options_dates) > 0:
            first_exp = options_dates[0]
            calls = stock.option_chain(first_exp).calls

            return (
                f"""Options Availability for {ticker}:
- Options Available: ✓ YES
- Number of Expirations: {len(options_dates)}
- Next Expiration: {first_exp}
- Call Options Available: {len(calls)}
- Options are tradeable: ✓ CONFIRMED
"""
            )
        else:
            return f"Options Availability for {ticker}: ✗ NO OPTIONS AVAILABLE"
    except Exception as e:
        return f"Error checking options for {ticker}: {str(e)}"
