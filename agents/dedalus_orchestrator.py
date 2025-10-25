from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
import os
from .prompts import SYSTEM_PROMPT

load_dotenv()


class StockAnalysisAgent:
    def __init__(self):
        self.client = AsyncDedalus(api_key=os.getenv("DEDALUS_API_KEY"))
        self.runner = DedalusRunner(self.client)
        self.conversation_history = []

    async def chat(self, user_message: str):
        """Process user message and orchestrate tool calls via Dedalus"""

        # Use Dedalus Runner with MCP servers
        result = await self.runner.run(
            input=user_message,
            model=[
                "gemini/gemini-1.5-pro-latest",
                "anthropic/claude-3-5-sonnet-20240620",
            ],
            mcp_servers=[
                "financial-data-server",  # Our deployed MCP server
                "edgar-server",  # Our deployed MCP server
                "windsor/brave-search-mcp",  # Dedalus marketplace tool
            ],
            system_prompt=SYSTEM_PROMPT,
            stream=False,
        )

        return result.final_output
