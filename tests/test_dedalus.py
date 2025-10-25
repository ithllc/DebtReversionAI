import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Mock the dedalus_labs library before importing the agent
# This is necessary because we don't have the real library installed
# or configured in the test environment.
mock_dedalus = MagicMock()
# We need to make sure the classes exist on the mock
mock_dedalus.AsyncDedalus = MagicMock()
mock_dedalus.DedalusRunner = MagicMock()

with patch.dict("sys.modules", {"dedalus_labs": mock_dedalus, "dotenv": MagicMock()}):
    from agents.dedalus_orchestrator import StockAnalysisAgent
    from agents.prompts import SYSTEM_PROMPT


@pytest.fixture
def mock_env():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {"DEDALUS_API_KEY": "test_key"}):
        yield


def test_agent_initialization(mock_env):
    """Tests that the StockAnalysisAgent initializes correctly."""

    # We need to reset mocks because they are stateful across tests
    mock_dedalus.AsyncDedalus.reset_mock()
    mock_dedalus.DedalusRunner.reset_mock()

    agent = StockAnalysisAgent()

    # Assert that the Dedalus client and runner are instantiated
    mock_dedalus.AsyncDedalus.assert_called_once_with(api_key="test_key")
    mock_dedalus.DedalusRunner.assert_called_once_with(
        mock_dedalus.AsyncDedalus.return_value
    )

    assert agent.client is not None
    assert agent.runner is not None
    assert agent.client == mock_dedalus.AsyncDedalus.return_value
    assert agent.runner == mock_dedalus.DedalusRunner.return_value


@pytest.mark.asyncio
async def test_agent_chat_call(mock_env):
    """Tests that the agent's chat method calls the DedalusRunner correctly."""

    # Reset mocks for a clean test
    mock_dedalus.AsyncDedalus.reset_mock()
    mock_dedalus.DedalusRunner.reset_mock()

    agent = StockAnalysisAgent()

    # Configure the mock runner to return a specific result
    mock_run_result = MagicMock()
    mock_run_result.final_output = "This is the final AI response."

    # The runner's run method is async, so we use AsyncMock
    agent.runner.run = AsyncMock(return_value=mock_run_result)

    user_message = "Find me some stocks."
    response = await agent.chat(user_message)

    # Assert the response is what we configured the mock to return
    assert response == "This is the final AI response."

    # Assert that the runner was called with the correct arguments
    agent.runner.run.assert_awaited_once_with(
        input=user_message,
        model=["gemini/gemini-1.5-pro-latest", "anthropic/claude-3-5-sonnet-20240620"],
        mcp_servers=[
            "financial-data-server",
            "edgar-server",
            "windsor/brave-search-mcp",
        ],
        system_prompt=SYSTEM_PROMPT,
        stream=False,
    )
