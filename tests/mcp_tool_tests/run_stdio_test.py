#!/usr/bin/env python3
"""Run an end-to-end MCP test over STDIO.

This script starts the MCP server entrypoint in STDIO mode using the project's
virtualenv, sends a JSON-RPC initialize and a tool call over the server's stdin,
reads responses from stdout, and then shuts down the server.

Note: This is a development/debug helper. It assumes the project's virtualenv
is at /llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python
as used elsewhere in this workspace.
"""
import json
import os
import subprocess
import sys
import time
import selectors


VENV_PYTHON = os.environ.get('AITINKERERS_VENV_PYTHON',
                              '/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python')
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def start_server_stdio():
    cmd = [VENV_PYTHON, '-m', 'DebtReversionAI.src.main', '--stdio']
    env = os.environ.copy()
    env['PYTHONPATH'] = REPO_ROOT + (':' + env.get('PYTHONPATH', '') if env.get('PYTHONPATH') else '')

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, bufsize=1)
    return proc


def write_jsonrpc(proc, obj):
    data = json.dumps(obj)
    proc.stdin.write(data + "\n")
    proc.stdin.flush()


def read_responses(proc, timeout=20, expected_ids=None):
    """
    Read lines from the server stdout/stderr until timeout or until we have seen
    JSON responses with all ids in expected_ids (if provided).

    Returns (out_lines, parsed_messages) where parsed_messages is a list of
    parsed JSON objects (may be empty).
    """
    if expected_ids is None:
        expected_ids = []

    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    sel.register(proc.stderr, selectors.EVENT_READ)

    deadline = time.time() + timeout
    out_lines = []
    parsed = []
    seen_ids = set()
    while time.time() < deadline:
        events = sel.select(timeout=1)
        for key, _mask in events:
            line = key.fileobj.readline()
            if not line:
                continue
            out_lines.append(line.rstrip('\n'))
            # Try to parse JSON from the line
            try:
                j = json.loads(line)
                parsed.append(j)
                # If this looks like a JSON-RPC message with an id, track it
                if isinstance(j, dict) and 'id' in j:
                    seen_ids.add(j['id'])
                # If we've seen all expected ids, return early
                if expected_ids and set(expected_ids).issubset(seen_ids):
                    return out_lines, parsed
            except Exception:
                # Not a JSON line — ignore
                pass
    return out_lines, parsed


def main():
    print('Starting MCP server (stdio) using virtualenv python:', VENV_PYTHON)
    proc = start_server_stdio()
    try:
        # Give server a moment to initialize
        time.sleep(1.0)

        # Initialize — use the expected InitializeRequest shape
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                # Use a recent MCP protocol version string the server bindings expose.
                # The server's pydantic model accepts str or int; use a recent date-based
                # protocol version to match expectations.
                "protocolVersion": "2025-06-18",
                # Capabilities may be empty; the server accepts extra fields.
                "capabilities": {},
                # clientInfo must include a version field (Implementation model).
                "clientInfo": {"name": "stdio_test", "version": "1.0"}
            },
            "id": 1,
        }
        print('Sending initialize...')
        write_jsonrpc(proc, init_msg)

        # Call tool get_stock_data_range for BYND exact dates
        # Use the server-expected tools/call method and params
        call_msg = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_stock_data_range",
                # server commonly expects `arguments` (or `args`); use `arguments` per schema
                "arguments": {"ticker": "BYND", "start": "2025-10-13", "end": "2025-10-18"}
            },
            "id": 2,
        }
        print('Sending tool call...')
        write_jsonrpc(proc, call_msg)

        print('Reading responses (timeout 30s)...')
        # Wait for both the initialize response (id 1) and the tool call response (id 2)
        out_lines, parsed = read_responses(proc, timeout=30, expected_ids=[1, 2])

        print('\n--- STDIO output (partial) ---')
        for l in out_lines:
            print(l)
        print('--- end output ---\n')

        if parsed:
            print('Parsed JSON responses:')
            for p in parsed:
                try:
                    print(json.dumps(p, indent=2))
                except Exception:
                    print(repr(p))
        else:
            print('No JSON responses parsed from stdout within timeout.')

    finally:
        # Try to terminate the server
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == '__main__':
    main()
