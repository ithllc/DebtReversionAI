import asyncio
import os
from servers.edgar_server import EdgarServer
from servers.financial_server import FinancialDataServer

async def main():
    """
    Main entrypoint to run all MCP servers concurrently.
    Dedalus Labs platform looks for this src/main.py file to start the servers.
    """
    print("Starting MCP servers...")

    # Set the SEC_API_USER_AGENT from environment variables for the Edgar server
    # This is crucial for the Edgar server to identify itself to the SEC.
    sec_identity = os.getenv("SEC_API_USER_AGENT")
    if not sec_identity:
        raise ValueError("SEC_API_USER_AGENT environment variable is not set. Please set it to a valid email address.")

    # Instantiate the servers, assigning them to different ports
    financial_server = FinancialDataServer(port=8000)
    edgar_server = EdgarServer(port=8001)

    print("Launching Financial Data Server on port 8000...")
    financial_task = asyncio.create_task(financial_server.server.run())

    print("Launching Edgar Data Server on port 8001...")
    edgar_task = asyncio.create_task(edgar_server.server.run())

    print("All MCP servers are running.")
    
    # Keep the main function alive to allow servers to run
    await asyncio.gather(financial_task, edgar_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down servers.")