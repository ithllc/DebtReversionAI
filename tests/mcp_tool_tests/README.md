# MCP Tool Tests (streamable + BYND exact-range)

Purpose
-------
These are small test utilities used during local development to validate two things:

- The financial tool logic (exact-date range fetch for ticker BYND) works correctly.
- The MCP streamable-HTTP transport (initialize + SSE GET + tool call) is operable against the running MCP server.

Files in this folder
--------------------
- `tools_test_bynd_exact.py` — simple script that uses `yfinance` to fetch BYND data for an exact date range and prints a summary; also contains a best-effort HTTP POST probe to the MCP `/mcp` endpoint.
- `tools_streamable_client.py` — a small client that uses the SDK's streamable-HTTP helper (`streamablehttp_client` + `ClientSession`) to initialize a session, open the SSE stream, and call `get_stock_data_range` as a tool.
- `tools_streamable_client.out` — captured output from a previous run of the streamable client (keeps artifacts for debugging).
- `server_ephemeral.log` and `server_ephemeral.pid` — logs and pid from the ephemeral MCP server used during tests.

Why this test was conducted
---------------------------
The streamable-HTTP transport is timing-sensitive: clients must perform an initialize POST, capture the server session id, open an SSE GET with the session id and Accept: text/event-stream, and then POST tool calls while the SSE stream remains open. We created these scripts to:

1. Validate the tool logic independently (fast feedback without the MCP transport).
2. Exercise the full streamable protocol end-to-end and capture logs to debug 406/400 errors and blocking behavior observed with the SDK helper.

How to run these tests
----------------------

Prerequisites
- Activate the virtualenv used for the project. Example (adjust path as needed):

```bash
export PYTHONPATH=/llm_models_python_code_src/DebtReversionAI:$PYTHONPATH
/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python -m pip install -r requirements.txt
```

1) Run the fast tool-only check (no MCP required):

```bash
export PYTHONPATH=/llm_models_python_code_src/DebtReversionAI:$PYTHONPATH
/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python /llm_models_python_code_src/DebtReversionAI/tests/mcp_tool_tests/tools_test_bynd_exact.py
```

2) Test the streamable transport (explicit flow with curl) — quick manual verification:

```bash
# POST initialize and capture mcp-session-id
curl -i -X POST "http://127.0.0.1:<PORT>/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","params":{"client_name":"test_client"},"id":1}'

# Open SSE GET (in another shell) — include the mcp-session-id header returned by the init call
curl -N -H "Accept: text/event-stream" -H "mcp-session-id: <SESSION_ID>" "http://127.0.0.1:<PORT>/mcp"

# POST the tool call while the SSE GET is open (use the same session id)
curl -i -X POST "http://127.0.0.1:<PORT>/mcp" -H "Content-Type: application/json" -H "mcp-session-id: <SESSION_ID>" -d '{"jsonrpc":"2.0","method":"call_tool","params":{"tool":"get_stock_data_range","args":{"ticker":"BYND","start":"2025-10-13","end":"2025-10-18"}},"id":1}'
```

3) Run the SDK-based streamable client (may block if timing mismatches exist):

```bash
export PYTHONPATH=/llm_models_python_code_src/DebtReversionAI:$PYTHONPATH
export MCP_ENDPOINT="http://127.0.0.1:<PORT>/mcp"
timeout 60s /llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python /llm_models_python_code_src/DebtReversionAI/tests/mcp_tool_tests/tools_streamable_client.py

4) STDIO end-to-end JSON-RPC test (search -> convert_to_markdown, get_recent_filings -> convert_to_markdown)

This script starts the MCP server in `stdio` mode, issues `search_debt_conversions` and
`get_recent_filings` tool calls for ticker `BYND`, and then calls `convert_to_markdown` in
both `snippet` and `chunked` modes for each result. It prints the raw JSON-RPC messages
received from the server.

Run it from the repo root using the project venv and set `SEC_API_USER_AGENT` (the MCP server
requires this env var to start):

```bash
export PYTHONPATH=/llm_models_python_code_src/DebtReversionAI:$PYTHONPATH
export SEC_API_USER_AGENT="dev@example.com"
/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python \
	/llm_models_python_code_src/DebtReversionAI/tests/mcp_tool_tests/run_stdio_test_edgar.py
```

Note: the test makes external network requests (EDGAR / yfinance). Expect run times of several
seconds depending on network and SEC API behavior. If you only want to exercise the local
conversion flow, run `run_stdio_test_edgar.py` but mock or stub the network calls in your
environment.
```

Notes
- Replace `<PORT>` with the port the server is listening on (check `server_ephemeral.log` or the MCP startup output).
- The scripts are test utilities and not intended for production. Keep them under `tests/mcp_tool_tests` for future debugging and demonstration runs.

Contact
- If the streamable client blocks, perform the curl-based manual flow to verify the server's session behavior. The curl flow gives the clearest, low-level evidence of success.
