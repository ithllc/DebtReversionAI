#!/usr/bin/env python
"""
PROPOSED FIX: MCP Server Entry Point Wrapper for Dedalus Labs Deployment

This file demonstrates the proposed replacement for /DebtReversionAI/main.py

PURPOSE:
--------
When deployed to Dedalus Labs, the platform executes `uv run main`, which 
runs the root main.py file. This wrapper ensures that the actual MCP server
(located in src/main.py) is started instead of the agent orchestrator.

CURRENT PROBLEM:
----------------
The existing main.py starts the StockAnalysisAgent (client-side), which then
tries to connect to the MCP server 'ficonnectme2anymcp/DebtReversionAI'.
However, the MCP server itself never starts because src/main.py is never called.

SOLUTION:
---------
This wrapper:
1. Sets up the Python path to include the project root
2. Imports the actual MCP server's main function from src/main.py
3. Runs the server asynchronously
4. Provides clear error messages if something goes wrong

DEPLOYMENT STEPS:
-----------------
1. Rename current main.py to: agent_runner.py
   (This preserves your agent for local testing)

2. Copy this file to: main.py
   (This becomes the new entry point for Dedalus)

3. Update pyproject.toml to add:
   [project.scripts]
   main = "main:main"

4. Redeploy to Dedalus Labs

WHAT HAPPENS AFTER FIX:
-----------------------
Dedalus runs: uv run main
    ↓
Executes: main.py (this wrapper)
    ↓
Imports and runs: src/main.py (the MCP server)
    ↓
Server starts and listens for tool calls via stdio
    ↓
LLM can now use: check_52week_low, calculate_macd, etc.

TESTING LOCALLY:
----------------
After applying this fix, test locally with:
  uv run main

You should see:
  "Starting unified DebtReversionAI MCP server..."
  "Launching unified DebtReversionAI server via stdio transport..."

NOT:
  "🤖 DebtReversionAI - Powered by Dedalus Labs + Manus AI"
  (That's the agent, not the server)
"""

import sys
import os
import asyncio


def main():
    """
    Main function for script entry point.
    
    This is the entry point that Dedalus Labs will execute when running
    `uv run main`. It ensures the MCP server starts correctly.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Ensure the project root is in the Python path
    # This allows imports like "from src.main import main"
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print("=" * 70)
    print("🚀 DebtReversionAI MCP Server - Entry Point Wrapper")
    print("=" * 70)
    print(f"📁 Project Root: {project_root}")
    print(f"🐍 Python: {sys.version}")
    print(f"📂 Working Directory: {os.getcwd()}")
    print("=" * 70)
    
    try:
        # Import the actual MCP server's main function
        # This comes from src/main.py which contains the UnifiedDebtReversionServer
        print("📦 Importing MCP server from src/main.py...")
        from src.main import main as server_main
        
        print("✅ Import successful!")
        print("🔧 Starting MCP server (async)...")
        print("=" * 70)
        
        # Run the async server main function
        # src/main.py's main() function is async and runs the MCP server
        exit_code = asyncio.run(server_main())
        
        # If we get here, the server exited cleanly
        print("=" * 70)
        print("✅ MCP Server shut down cleanly")
        print("=" * 70)
        return exit_code if exit_code is not None else 0
        
    except ImportError as e:
        # This happens if src/main.py doesn't exist or has import errors
        print("❌ ERROR: Failed to import MCP server")
        print("=" * 70)
        print(f"Import Error: {e}")
        print("")
        print("Possible causes:")
        print("  1. src/main.py file is missing")
        print("  2. Missing dependencies in the virtual environment")
        print("  3. Syntax errors in src/main.py")
        print("")
        print("Please check:")
        print(f"  - File exists: {os.path.join(project_root, 'src', 'main.py')}")
        print("  - Dependencies installed: pip install -r requirements.txt")
        print("=" * 70)
        
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    except Exception as e:
        # Catch any other errors during server startup
        print("❌ ERROR: MCP server failed to start")
        print("=" * 70)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("")
        print("Common issues:")
        print("  1. Missing environment variable: SEC_API_USER_AGENT")
        print("  2. Port already in use (if using port mode)")
        print("  3. Permission errors with file access")
        print("")
        print("Stack trace:")
        print("=" * 70)
        
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    """
    Script entry point.
    
    When Dedalus runs `uv run main`, Python executes this block,
    which calls the main() function above.
    """
    sys.exit(main())
