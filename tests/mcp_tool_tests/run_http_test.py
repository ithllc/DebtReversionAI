#!/usr/bin/env python3
"""Run an end-to-end MCP test over HTTP (non-streaming probe).

This script starts the MCP server on a chosen port using the project's virtualenv,
waits for the server to be available, sends a best-effort JSON-RPC POST to call
the `get_stock_data_range` tool, prints the response, and then shuts down the server.

Note: The server's streamable transport may prefer a session/SSE flow. This script
attempts a single POST call which some FastMCP HTTP handlers accept for simple
testing. If the server returns 406/other, see the README for the proper streamable flow.
"""
import json
import os
import subprocess
import sys
import time
from urllib import request, error


VENV_PYTHON = os.environ.get('AITINKERERS_VENV_PYTHON',
                              '/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python')
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def start_server_port(port: int):
    cmd = [VENV_PYTHON, '-m', 'DebtReversionAI.src.main', '--port', str(port)]
    env = os.environ.copy()
    env['PYTHONPATH'] = REPO_ROOT + (':' + env.get('PYTHONPATH', '') if env.get('PYTHONPATH') else '')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
    return proc


def wait_for_http(port: int, timeout: int = 10):
    deadline = time.time() + timeout
    url = f'http://127.0.0.1:{port}/'
    while time.time() < deadline:
        try:
            with request.urlopen(url, timeout=1) as resp:
                return True
        except Exception:
            time.sleep(0.5)
    return False


def call_tool_http(port: int):
    url = f'http://127.0.0.1:{port}/mcp'
    payload = {
        "jsonrpc": "2.0",
        "method": "call_tool",
        "params": {"tool": "get_stock_data_range", "args": {"ticker": "BYND", "start": "2025-10-13", "end": "2025-10-18"}},
        "id": 1,
    }
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode('utf-8')
            print('HTTP response status:', resp.status)
            print('HTTP response body:')
            print(body)
    except error.HTTPError as he:
        print('HTTPError:', he.code, he.reason)
        try:
            print(he.read().decode('utf-8'))
        except Exception:
            pass
    except Exception as e:
        print('HTTP request failed:', repr(e))


def main():
    port = 39776
    print('Starting MCP server (http) on port', port)
    proc = start_server_port(port)
    try:
        ok = wait_for_http(port, timeout=10)
        if not ok:
            print('Server did not become available on port', port)
            # print some stderr for debugging
            try:
                stderr = proc.stderr.read()
                print('Server stderr (partial):')
                print(stderr)
            except Exception:
                pass
            return

        print('Server is up — performing HTTP tool call...')
        call_tool_http(port)

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == '__main__':
    main()
