import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys

# Placeholder for financial data server tests
# The class we are testing is in a file that has not been created yet.
# This is a placeholder for the actual import.
# from mcp_servers.financial_server import FinancialDataServer


# Mocking the mcp library as it is not available locally
class MockTextContent:
    def __init__(self, type, text):
        self.type = type
        self.text = text


class MockTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


class MockServer:
    def __init__(self, name):
        self.name = name
        self._tool_defs = []
        self._tool_impls = {}

    def list_tools(self):
        def decorator(f):
            self._tool_defs.append(f)
            return f

        return decorator

    def call_tool(self):
        def decorator(f):
            self._tool_impls["call_tool"] = f
            return f

        return decorator


# Since mcp.server is not a real installable library, we patch it.
with patch.dict(
    "sys.modules",
    {"mcp": MagicMock(), "mcp.server": MagicMock(), "mcp.types": MagicMock()},
):
    # Replace with our mock implementations
    sys.modules["mcp.server"].Server = MockServer
    sys.modules["mcp.types"].Tool = MockTool
    sys.modules["mcp.types"].TextContent = MockTextContent

    from mcp_servers.financial_server import FinancialDataServer


@pytest.fixture(autouse=True)
def mock_yfinance_cache():
    """Mocks yfinance.cache to prevent network calls and caching errors."""
    with patch("yfinance.cache") as mock_cache:
        mock_cache.get_yh_cache_dir.return_value = "/tmp/yfinance_cache"
        yield


@pytest.fixture
def financial_server():
    """Provides an instance of the FinancialDataServer for testing."""
    # No special setup needed if yfinance.Ticker is properly mocked in each test
    server = FinancialDataServer()
    return server


@pytest.mark.asyncio
async def test_get_stock_data(financial_server):
    """Tests the _get_stock_data method."""
    mock_ticker = MagicMock()
    mock_history = pd.DataFrame(
        {"Close": [100, 102, 101.5], "High": [103, 104, 102], "Low": [99, 101, 100]}
    )
    mock_ticker.history.return_value = mock_history

    with patch("yfinance.Ticker", return_value=mock_ticker) as mock_yf_ticker:
        result = await financial_server._get_stock_data("AAPL", "1y")

        mock_yf_ticker.assert_called_with("AAPL")
        mock_ticker.history.assert_called_with(period="1y")

        assert len(result) == 1
        text = result[0].text
        assert "Stock Data for AAPL" in text
        assert "Current Price: $101.50" in text
        assert "52-Week High: $104.00" in text
        assert "52-Week Low: $99.00" in text


@pytest.mark.asyncio
async def test_calculate_macd(financial_server):
    """Tests the _calculate_macd method."""
    mock_ticker = MagicMock()
    mock_history = pd.DataFrame({"Close": [100, 102, 101.5, 103, 105, 104]})
    mock_ticker.history.return_value = mock_history

    # Create a DataFrame with an index for the last row
    mock_macd_df = pd.DataFrame(
        {"MACD_12_26_9": [-0.5], "MACDs_12_26_9": [-0.4], "MACDh_12_26_9": [-0.1]},
        index=[5],
    )  # Assuming the last index is 5

    with (
        patch("yfinance.Ticker", return_value=mock_ticker) as mock_yf_ticker,
        patch("pandas_ta.macd", return_value=mock_macd_df) as mock_ta_macd,
    ):
        result = await financial_server._calculate_macd("MSFT", "daily")

        mock_yf_ticker.assert_called_with("MSFT")
        mock_ticker.history.assert_called_with(period="6mo", interval="1d")
        mock_ta_macd.assert_called_once()

        assert len(result) == 1
        text = result[0].text
        assert "MACD Analysis for MSFT (daily)" in text
        assert "Current Price: $104.00" in text
        assert "MACD Line: -0.5000" in text
        assert "Signal Line: -0.4000" in text
        assert "Histogram: -0.1000" in text
        assert "Signal: Bearish" in text


@pytest.mark.asyncio
async def test_check_52week_low_is_near(financial_server):
    """Tests _check_52week_low when price is near the low."""
    mock_ticker = MagicMock()
    mock_history = pd.DataFrame(
        {"Close": [110, 105, 101, 101.0], "Low": [108, 102, 100, 115]},
        index=[
            datetime(2023, 1, 1),
            datetime(2023, 2, 1),
            datetime(2023, 3, 1),
            datetime(2023, 4, 1),
        ],
    )
    # Ensure the history is not empty
    assert not mock_history.empty
    mock_ticker.history.return_value = mock_history

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await financial_server._check_52week_low("F", 0.05)  # 5% tolerance

        text = result[0].text
        assert "52-Week Low Analysis for F" in text
        assert "Current Price: $101.00" in text
        assert "52-Week Low: $100.00" in text
        assert "Near 52W Low: ✓ YES" in text
        assert "Distance: 1.00%" in text


@pytest.mark.asyncio
async def test_check_52week_low_is_not_near(financial_server):
    """Tests _check_52week_low when price is not near the low."""
    mock_ticker = MagicMock()
    mock_history = pd.DataFrame(
        {"Close": [110, 105, 101, 120], "Low": [108, 102, 100, 115]},
        index=[
            datetime(2023, 1, 1),
            datetime(2023, 2, 1),
            datetime(2023, 3, 1),
            datetime(2023, 4, 1),
        ],
    )
    # Ensure the history is not empty
    assert not mock_history.empty
    mock_ticker.history.return_value = mock_history

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await financial_server._check_52week_low("F", 0.05)  # 5% tolerance

        text = result[0].text
        assert "Near 52W Low: ✗ NO" in text
        assert "Distance: 20.00%" in text


@pytest.mark.asyncio
async def test_check_optionable_yes(financial_server):
    """Tests _check_optionable for a stock with options."""
    mock_ticker = MagicMock()
    mock_ticker.options = ("2025-11-21",)
    mock_option_chain = MagicMock()
    mock_option_chain.calls = pd.DataFrame({"strike": [100, 110]})
    mock_ticker.option_chain.return_value = mock_option_chain

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await financial_server._check_optionable("GOOG")
        text = result[0].text
        assert "Options Available: ✓ YES" in text
        assert "Number of Expirations: 1" in text


@pytest.mark.asyncio
async def test_check_optionable_no(financial_server):
    """Tests _check_optionable for a stock without options."""
    mock_ticker = MagicMock()
    mock_ticker.options = ()  # Empty tuple means no options

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await financial_server._check_optionable("NOPT")
        text = result[0].text
        assert "Options Availability for NOPT: ✗ NO OPTIONS AVAILABLE" in text
