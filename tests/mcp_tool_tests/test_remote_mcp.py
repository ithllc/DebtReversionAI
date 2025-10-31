#!/usr/bin/env python3
"""
Test script for invoking a tool on a remote Dedalus MCP server.

This script uses the StockAnalysisAgent to connect to a private MCP server
hosted on the Dedalus platform and executes a tool call to verify connectivity
and data retrieval. It requires the DEDALUS_API_KEY environment variable.
"""
import asyncio
import os
from agents.dedalus_orchestrator import StockAnalysisAgent

# The private MCP server endpoint provided by the user.
# This will be used to construct the full URL for the remote server.
PRIVATE_MCP_SERVER_NAME = "ficonnectme2anymcp/DebtReversionAI"


async def main():
    """
    Initializes the agent, connects to the remote MCP server, and runs a test.
    """
    print("🤖 Running Remote MCP Server Test...")
    print("=" * 60)

    # Check for the necessary API key.
    if not os.environ.get("DEDALUS_API_KEY"):
        print("❌ ERROR: DEDALUS_API_KEY environment variable not set.")
        print("Please set the API key to connect to the Dedalus platform.")
        return

    try:
        # 1. Instantiate the agent.
        # The agent's __init__ method should be configured to use remote servers.
        # We will pass the private server name to it.
        print(f"🔧 Initializing agent to connect to: {PRIVATE_MCP_SERVER_NAME}")
        agent = StockAnalysisAgent(remote_server_name=PRIVATE_MCP_SERVER_NAME)

        # 2. Prepare a tool call.
        # We will invoke the 'get_stock_data' tool as a direct test.
        tool_name = "get_stock_data"
        tool_params = {"symbol": "BYND"}
        
        print(f"📞 Invoking tool '{tool_name}' with params: {tool_params}")

        # 3. Use the agent's client to make the tool call.
        # This directly tests the tool invocation without going through the LLM.
        response = await agent.client.tools.call(tool_name, tool_params)

        # 4. Print the response from the remote server.
        print("\n✅ Remote Tool Call Successful!")
        print("=" * 60)
        print("Response from server:")
        print(response)
        print("=" * 60)
        print("\nConclusion: The agent can successfully connect to the remote MCP server and retrieve data.")

    except Exception as e:
        print(f"\n❌ An error occurred during the test: {e}")
        print("Please check the following:")
        print("  - Your DEDALUS_API_KEY is correct.")
        print(f"  - The private server name '{PRIVATE_MCP_SERVER_NAME}' is correct.")
        print("  - The remote server is running and accessible.")


if __name__ == "__main__":
    # To run this test, you must have the dedalus_orchestrator.py modified
    # to accept a remote_server_name and configure the mcp.Client accordingly.
    asyncio.run(main())
