#!/usr/bin/env python3
"""Streamable-HTTP client that initializes a session and calls get_stock_data_range.

This copy lives in tests/mcp_tool_tests for archival/debug runs.
"""
import asyncio
import os
import sys

from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession


async def main():
    endpoint = os.environ.get("MCP_ENDPOINT", "http://127.0.0.1:8080/mcp")
    print(f"Connecting to {endpoint} via Streamable HTTP...")

    try:
        async with streamablehttp_client(endpoint) as (read_stream, write_stream, get_session_id):
            print("streamablehttp_client context opened")
            session = ClientSession(read_stream, write_stream)

            try:
                sid = get_session_id()
                print("get_session_id() returned:", sid)
            except Exception:
                print("get_session_id() not available or raised an exception")

            try:
                print("Calling session.initialize()...")
                init_result = await session.initialize()
                print("Initialized session, server protocolVersion=", getattr(init_result, 'protocolVersion', None))
            except Exception as e:
                print("session.initialize() raised:", repr(e))
                raise

            ticker = "BYND"
            start = "2025-10-13"
            end = "2025-10-18"

            print(f"Calling tool get_stock_data_range for {ticker} {start}->{end} ...")
            try:
                result = await session.call_tool("get_stock_data_range", {"ticker": ticker, "start": start, "end": end})
            except Exception as e:
                print("session.call_tool() raised:", repr(e))
                raise

            try:
                if getattr(result, 'isError', False):
                    print("Tool returned error:", getattr(result, 'error', None))
                else:
                    print("Tool result (raw object):")
                    print(result)
                    try:
                        print('Result text/content:', getattr(result, 'text', None) or getattr(result, 'content', None))
                    except Exception:
                        pass
            except Exception as e:
                print("Error inspecting result:", repr(e))

            try:
                await session.send_ping()
            except Exception as e:
                print("session.send_ping() raised:", repr(e))
    except Exception as e:
        print("Streamable client encountered an error:", repr(e))
        raise


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print("Client error:", e)
        sys.exit(1)
