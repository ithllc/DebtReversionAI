from manus_sdk import ManusClient
import os


class ManusBrowser:
    def __init__(self):
        self.client = ManusClient(api_key=os.getenv("MANUS_API_KEY"))

    async def verify_options(self, ticker: str):
        """Use Manus AI to verify options availability"""
        prompt = (
            f"Navigate to Yahoo Finance and verify if {ticker} has options available"
        )
        result = await self.client.browse(prompt)
        return result

    async def search_financial_news(self, ticker: str, topic: str):
        """Use Manus AI to search for financial news"""
        prompt = f"Search for news about {ticker} related to {topic}"
        result = await self.client.search(prompt)
        return result

    async def extract_options_data(self, ticker: str):
        """Extract options chain data using Manus AI vision"""
        prompt = f"Go to Yahoo Finance options page for {ticker} and extract the options chain data"
        result = await self.client.browse(prompt, mode="vision")
        return result
