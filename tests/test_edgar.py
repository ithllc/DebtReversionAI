import pytest
from unittest.mock import MagicMock, patch
import os
import sys


# Mocking the mcp and edgar libraries as they are not available locally
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


# Since mcp.server and edgar are not real installable libraries in this context, we patch them.
with patch.dict(
    "sys.modules",
    {
        "mcp": MagicMock(),
        "mcp.server": MagicMock(),
        "mcp.types": MagicMock(),
        "edgar": MagicMock(),
    },
):

    # Replace with our mock implementations
    sys.modules["mcp.server"].Server = MockServer
    sys.modules["mcp.types"].Tool = MockTool
    sys.modules["mcp.types"].TextContent = MockTextContent

    from mcp_servers.edgar_server import EdgarServer


@pytest.fixture
def edgar_server():
    """Provides an instance of the EdgarServer for testing."""
    os.environ["SEC_API_USER_AGENT"] = "test@example.com"
    server = EdgarServer()
    return server


@pytest.mark.asyncio
async def test_search_debt_conversions_found(edgar_server):
    """Tests _search_debt_conversions when a conversion is found."""
    mock_filing = MagicMock()
    mock_filing.text.return_value = (
        "This filing contains a debt conversion at a price of $10.50."
    )
    mock_filing.filing_date = "2023-10-26"
    mock_filing.accession_no = "0001-2-3"
    mock_filing.url = "http://example.com/filing"

    mock_filings = MagicMock()
    mock_filings.filter.return_value = [mock_filing]

    mock_company = MagicMock()
    mock_company.get_filings.return_value = mock_filings

    with patch("edgar.Company", return_value=mock_company) as mock_edgar_company:
        result = await edgar_server._search_debt_conversions("TEST", 3)

        mock_edgar_company.assert_called_with("TEST")
        mock_company.get_filings.assert_called_with(form="8-K")

        assert len(result) == 1
        text = result[0].text
        assert "Found 1 potential conversion events" in text
        assert "Date: 2023-10-26" in text
        assert "Conversion Price: $10.5" in text
        assert "URL: http://example.com/filing" in text


@pytest.mark.asyncio
async def test_search_debt_conversions_not_found(edgar_server):
    """Tests _search_debt_conversions when no conversion is found."""
    mock_filing = MagicMock()
    mock_filing.text.return_value = "This filing is about something else entirely."

    mock_filings = MagicMock()
    mock_filings.filter.return_value = [mock_filing]

    mock_company = MagicMock()
    mock_company.get_filings.return_value = mock_filings

    with patch("edgar.Company", return_value=mock_company):
        result = await edgar_server._search_debt_conversions("TEST", 3)
        text = result[0].text
        assert "Found 0 potential conversion events" in text


def test_extract_price(edgar_server):
    """Tests the internal _extract_price method."""
    text_with_price = "The conversion price is $5.50 per share."
    assert edgar_server._extract_price(text_with_price) == 5.5

    text_with_int_price = "The price is $100."
    assert edgar_server._extract_price(text_with_int_price) == 100.0

    text_without_price = "There is no price here."
    assert edgar_server._extract_price(text_without_price) is None

    text_with_multiple_prices = "A price of $10 and another of $20. We take the first."
    assert edgar_server._extract_price(text_with_multiple_prices) == 10.0


@pytest.mark.asyncio
async def test_get_8k_filings(edgar_server):
    """Tests the _get_8k_filings method."""
    mock_filing = MagicMock()
    mock_filing.filing_date = "2023-10-27"
    mock_filing.form = "8-K"
    mock_filing.accession_no = "0004-5-6"
    mock_filing.url = "http://example.com/filing2"

    mock_company = MagicMock()
    # Slicing is used in the method, so the mock needs to support it
    type(mock_company.get_filings.return_value).__getitem__ = lambda _, s: [mock_filing]

    with patch("edgar.Company", return_value=mock_company) as mock_edgar_company:
        result = await edgar_server._get_8k_filings("XYZ", limit=1)

        mock_edgar_company.assert_called_with("XYZ")

        text = result[0].text
        assert "Recent 8-K Filings for XYZ" in text
        assert "- 2023-10-27: 8-K" in text
        assert "Accession: 0004-5-6" in text
        assert "URL: http://example.com/filing2" in text
