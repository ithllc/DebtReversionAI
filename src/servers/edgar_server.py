from mcp.server import Server
from mcp.types import Tool, TextContent
from edgar import Company, set_identity
from datetime import datetime, timedelta
import os
import re


class EdgarServer:
    def __init__(self, port=8001):
        self.server = Server("edgar-data", port=port)
        # Set SEC identity (required)
        set_identity(os.getenv("SEC_API_USER_AGENT"))
        self._register_tools()

    def _register_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [
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
                    name="get_8k_filings",
                    description="Get recent 8-K filings for a company",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["ticker"],
                    },
                ),
                Tool(
                    name="extract_conversion_terms",
                    description="Extract debt conversion terms from filing",
                    inputSchema={
                        "type": "object",
                        "properties": {"filing_url": {"type": "string"}},
                        "required": ["filing_url"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "search_debt_conversions":
                return await self._search_debt_conversions(
                    arguments["ticker"], arguments.get("months_back", 3)
                )
            elif name == "get_8k_filings":
                return await self._get_8k_filings(
                    arguments["ticker"], arguments.get("limit", 10)
                )
            elif name == "extract_conversion_terms":
                return await self._extract_conversion_terms(arguments["filing_url"])

    async def _search_debt_conversions(self, ticker: str, months_back: int):
        """Search for debt conversion events"""
        try:
            company = Company(ticker)

            # Get 8-K filings from last N months
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            filings = company.get_filings(form="8-K").filter(
                date=f"{cutoff_date.strftime('%Y-%m-%d')}:"
            )

            conversions = []
            keywords = [
                "conversion",
                "convertible",
                "debt conversion",
                "note conversion",
                "debenture",
            ]

            for filing in filings[:20]:  # Check first 20 filings
                text = filing.text().lower()

                # Check for conversion keywords
                if any(keyword in text for keyword in keywords):
                    # Try to extract conversion price
                    conversion_price = self._extract_price(text)

                    conversions.append(
                        {
                            "date": filing.filing_date,
                            "accession": filing.accession_no,
                            "url": filing.url,
                            "conversion_price": conversion_price,
                        }
                    )

            result = (
                f"Debt Conversion Search for {ticker} (Last {months_back} months):\n"
            )
            result += f"Found {len(conversions)} potential conversion events\n\n"

            for conv in conversions:
                result += f"- Date: {conv['date']}\n"
                result += f"  Accession: {conv['accession']}\n"
                if conv["conversion_price"]:
                    result += f"  Conversion Price: ${conv['conversion_price']}\n"
                result += f"  URL: {conv['url']}\n\n"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error searching conversions for {ticker}: {str(e)}",
                )
            ]

    async def _get_8k_filings(self, ticker: str, limit: int):
        """Get recent 8-K filings"""
        try:
            company = Company(ticker)
            filings = company.get_filings(form="8-K")[:limit]

            result = f"Recent 8-K Filings for {ticker}:\n\n"
            for filing in filings:
                result += f"- {filing.filing_date}: {filing.form}\n"
                result += f"  Accession: {filing.accession_no}\n"
                result += f"  URL: {filing.url}\n\n"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error getting 8-K filings for {ticker}: {str(e)}",
                )
            ]

    def _extract_price(self, text: str):
        """Extract price from filing text"""
        # Look for price patterns like $X.XX or $X
        price_pattern = r"\$(\d+\.?\d*)"
        matches = re.findall(price_pattern, text)

        if matches:
            # Return first reasonable price found
            prices = [float(p) for p in matches if 0.01 < float(p) < 10000]
            return prices[0] if prices else None
        return None

    async def _extract_conversion_terms(self, filing_url: str):
        """Extract detailed conversion terms from filing"""
        # This would parse the filing for detailed terms
        return [
            TextContent(
                type="text", text="Conversion term extraction not yet implemented"
            )
        ]
