import asyncio
from agents.dedalus_orchestrator import StockAnalysisAgent
from interface.chat import ChatInterface


async def main():
    print("🤖 DebtReversionAI - Powered by Dedalus Labs + Manus AI")
    print("=" * 60)
    print("Find mean reversion opportunities at 52-week lows")
    print("with recent debt conversions\n")
    print("Technologies: Dedalus MCP Gateway | Manus AI Browser")
    print("=" * 60)

    agent = StockAnalysisAgent()
    # The ManusBrowser is integrated within the agent's tools via MCP servers,
    # but we can instantiate it here if we need direct access.
    # browser = ManusBrowser()

    chat_interface = ChatInterface(agent)

    print("\n✅ Agent ready! Type 'quit' to exit.")
    print("💡 Try: 'Find stocks at 52-week lows with debt conversions'\n")

    await chat_interface.start()


if __name__ == "__main__":
    # Note: mcp.server is not a real library I can install.
    # The hackathon docs imply that these server files are deployed to Dedalus.
    # To run this locally, we would need to mock the MCP servers or have a way to run them.
    # For now, this main.py sets up the agent and a chat interface.
    # Running it will start the chat loop, but tool calls will fail without the deployed MCP servers.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
