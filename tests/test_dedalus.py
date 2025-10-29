import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Mock the dedalus_labs library before importing the agent
# This is necessary because we don't have the real library installed
# or configured in the test environment.
mock_dedalus = MagicMock()
# We need to make sure the classes exist on the mock
mock_dedalus.AsyncDedalus = MagicMock()
mock_dedalus.DedalusRunner = MagicMock()
mock_dedalus.Dedalus = MagicMock()

# Mock dotenv
mock_dotenv = MagicMock()

with patch.dict("sys.modules", {
    "dedalus_labs": mock_dedalus, 
    "dedalus_labs.lib.runner": mock_dedalus,
    "dotenv": mock_dotenv
}):
    from agents.dedalus_orchestrator import StockAnalysisAgent, RateLimiter
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
    mock_dedalus.Dedalus.reset_mock()

    agent = StockAnalysisAgent()

    # Assert that the Dedalus client is instantiated
    mock_dedalus.AsyncDedalus.assert_called_once_with(
        api_key="test_key",
        timeout=480.0
    )
    
    # Assert DedalusRunner is instantiated if available
    assert agent.client is not None
    assert agent.client == mock_dedalus.AsyncDedalus.return_value
    
    # Verify rate limiter is initialized
    assert agent.rate_limiter is not None
    assert isinstance(agent.rate_limiter, RateLimiter)


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
    agent.runner = MagicMock()
    agent.runner.run = AsyncMock(return_value=mock_run_result)

    user_message = "Find me some stocks."
    response = await agent.chat(user_message)

    # Assert the response contains the model-used prefix and output
    assert "[model_used=" in response
    assert "This is the final AI response." in response

    # Assert that the runner was called
    agent.runner.run.assert_awaited_once()
    
    # Verify the call included the correct MCP servers
    call_kwargs = agent.runner.run.call_args.kwargs
    assert "ficonnectme2anymcp/DebtReversionAI" in call_kwargs["mcp_servers"]
    assert "windsor/brave-search-mcp" in call_kwargs["mcp_servers"]
    assert call_kwargs["input"] == user_message
    assert call_kwargs["stream"] == False


@pytest.mark.asyncio
async def test_agent_rate_limiting(mock_env):
    """Tests that the agent enforces rate limiting."""
    agent = StockAnalysisAgent()
    
    # Mock the runner
    agent.runner = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.final_output = "Response"
    agent.runner.run = AsyncMock(return_value=mock_run_result)
    
    # Make many requests to trigger rate limit
    user_id = "test_user"
    for i in range(10):
        response = await agent.chat(f"Query {i}", user_id=user_id)
        assert "Response" in response or "model_used" in response
    
    # 11th request should be rate limited
    response = await agent.chat("Query 11", user_id=user_id)
    assert "Rate limit exceeded" in response
    assert "seconds" in response


@pytest.mark.asyncio  
async def test_agent_list_available_tools(mock_env):
    """Tests that the agent can list available tools from MCP server."""
    agent = StockAnalysisAgent()
    
    # Mock the runner with list_tools method
    agent.runner = MagicMock()
    mock_tools = [
        {"name": "check_52week_low", "description": "Check 52-week low"},
        {"name": "calculate_macd", "description": "Calculate MACD"}
    ]
    agent.runner.list_tools = AsyncMock(return_value=mock_tools)
    
    result = await agent.list_available_tools()
    
    assert result == mock_tools
    agent.runner.list_tools.assert_awaited_once_with(
        mcp_servers=["ficonnectme2anymcp/DebtReversionAI"]
    )


def test_rate_limiter():
    """Tests the RateLimiter class."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # First 3 requests should be allowed
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user1") == True
    
    # 4th request should be denied
    assert limiter.is_allowed("user1") == False
    
    # Different user should be allowed
    assert limiter.is_allowed("user2") == True
    
    # Check reset time
    reset_time = limiter.get_reset_time("user1")
    assert reset_time > 0 and reset_time <= 60
