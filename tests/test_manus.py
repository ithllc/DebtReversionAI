import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
from agents.manus_browser import ManusBrowser


@pytest.fixture
def mock_env():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {"MANUS_API_KEY": "test_manus_key"}):
        yield


@patch("agents.manus_browser.OpenAI")
def test_manus_browser_initialization(mock_openai, mock_env):
    """Tests that the ManusBrowser initializes the OpenAI client correctly."""
    browser = ManusBrowser()

    mock_openai.assert_called_once_with(
        base_url="https://api.manus.im",
        api_key="placeholder",
        default_headers={"API_KEY": "test_manus_key"},
    )
    assert browser.client is not None
    assert browser.client == mock_openai.return_value


@pytest.mark.asyncio
@patch("agents.manus_browser.asyncio.to_thread")
async def test_verify_options(mock_to_thread, mock_env):
    """Tests the verify_options method."""
    # Mock the response object that should be returned by the create() call
    mock_response = MagicMock()
    mock_response.id = "task_123"
    # This is the value that the inner 'create_task' function will return
    mock_to_thread.return_value = mock_response

    browser = ManusBrowser()
    # We are not testing the polling logic here, so we can mock the retrieve part
    browser.client.responses.retrieve = AsyncMock(
        return_value=MagicMock(
            status="completed",
            output=[
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "YES"}],
                }
            ],
        )
    )

    ticker = "AAPL"
    result = await browser.verify_options(ticker)

    assert result == "YES"
    mock_to_thread.assert_awaited_once()


@pytest.mark.asyncio
@patch("agents.manus_browser.asyncio.to_thread")
async def test_search_financial_news(mock_to_thread, mock_env):
    """Tests the search_financial_news method."""
    mock_response = MagicMock()
    mock_response.id = "task_456"
    mock_to_thread.return_value = mock_response

    browser = ManusBrowser()
    browser.client.responses.retrieve = AsyncMock(
        return_value=MagicMock(
            status="completed",
            output=[
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "News found."}],
                }
            ],
        )
    )

    ticker = "TSLA"
    topic = "earnings"
    result = await browser.search_financial_news(ticker, topic)

    assert result == "News found."
    mock_to_thread.assert_awaited_once()


@pytest.mark.asyncio
@patch("agents.manus_browser.asyncio.to_thread")
async def test_extract_options_data(mock_to_thread, mock_env):
    """Tests the extract_options_data method."""
    mock_response = MagicMock()
    mock_response.id = "task_789"
    mock_to_thread.return_value = mock_response

    browser = ManusBrowser()
    browser.client.responses.retrieve = AsyncMock(
        return_value=MagicMock(
            status="completed",
            output=[
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "{'data': '...'}"}],
                }
            ],
        )
    )

    ticker = "GOOG"
    result = await browser.extract_options_data(ticker)

    assert result == "{'data': '...'}"
    mock_to_thread.assert_awaited_once()
