import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Mock the manus_sdk library before importing the agent
mock_manus_sdk = MagicMock()
mock_manus_sdk.ManusClient = MagicMock()

with patch.dict("sys.modules", {"manus_sdk": mock_manus_sdk}):
    from agents.manus_browser import ManusBrowser


@pytest.fixture
def mock_env():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {"MANUS_API_KEY": "test_manus_key"}):
        yield


def test_manus_browser_initialization(mock_env):
    """Tests that the ManusBrowser initializes correctly."""
    mock_manus_sdk.ManusClient.reset_mock()

    browser = ManusBrowser()

    mock_manus_sdk.ManusClient.assert_called_once_with(api_key="test_manus_key")
    assert browser.client is not None
    assert browser.client == mock_manus_sdk.ManusClient.return_value


@pytest.mark.asyncio
async def test_verify_options(mock_env):
    """Tests the verify_options method."""
    mock_manus_sdk.ManusClient.reset_mock()
    browser = ManusBrowser()
    browser.client.browse = AsyncMock(return_value="Options are available.")

    ticker = "AAPL"
    result = await browser.verify_options(ticker)

    assert result == "Options are available."
    browser.client.browse.assert_awaited_once_with(
        f"Navigate to Yahoo Finance and verify if {ticker} has options available"
    )


@pytest.mark.asyncio
async def test_search_financial_news(mock_env):
    """Tests the search_financial_news method."""
    mock_manus_sdk.ManusClient.reset_mock()
    browser = ManusBrowser()
    browser.client.search = AsyncMock(return_value="News found.")

    ticker = "TSLA"
    topic = "earnings"
    result = await browser.search_financial_news(ticker, topic)

    assert result == "News found."
    browser.client.search.assert_awaited_once_with(
        f"Search for news about {ticker} related to {topic}"
    )


@pytest.mark.asyncio
async def test_extract_options_data(mock_env):
    """Tests the extract_options_data method with vision mode."""
    mock_manus_sdk.ManusClient.reset_mock()
    browser = ManusBrowser()
    browser.client.browse = AsyncMock(return_value="Options data extracted.")

    ticker = "GOOG"
    result = await browser.extract_options_data(ticker)

    assert result == "Options data extracted."
    browser.client.browse.assert_awaited_once_with(
        f"Go to Yahoo Finance options page for {ticker} and extract the options chain data",
        mode="vision",
    )
