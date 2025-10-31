#!/usr/bin/env python3
"""Run a small MCP STDIO test that calls search_debt_conversions.

This starts the MCP server in stdio mode, sends initialize, then calls
the `search_debt_conversions` tool and prints responses.
"""
import json
import os
import subprocess
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
            try:
                j = json.loads(line)
                parsed.append(j)
                if isinstance(j, dict) and 'id' in j:
                    seen_ids.add(j['id'])
                if expected_ids and set(expected_ids).issubset(seen_ids):
                    return out_lines, parsed
            except Exception:
                pass
    return out_lines, parsed


def main():
    print('Starting MCP server (stdio) using virtualenv python:', VENV_PYTHON)
    proc = start_server_stdio()
    try:
        time.sleep(1.0)

        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "stdio_edgar_test", "version": "1.0"}
            },
            "id": 1,
        }
        print('Sending initialize...')
        write_jsonrpc(proc, init_msg)

        call_msg = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_debt_conversions",
                "arguments": {"ticker": "BYND", "months_back": 6}
            },
            "id": 2,
        }
        print('Sending tool call search_debt_conversions...')
        write_jsonrpc(proc, call_msg)

        print('Reading responses for initialize + search (timeout 60s)...')
        out_lines, parsed = read_responses(proc, timeout=60, expected_ids=[1,2])

        print('\n--- STDIO output (partial) ---')
        for l in out_lines:
            print(l)
        print('--- end output ---\n')

        if parsed:
            print('Parsed JSON responses (initialize + search):')
            for p in parsed:
                try:
                    print(json.dumps(p, indent=2))
                except Exception:
                    print(repr(p))

        # Find the search result payload
        search_result = None
        for p in parsed:
            if isinstance(p, dict) and p.get('id') == 2:
                search_result = p.get('result')
                break

        # If we have a result, call convert_to_markdown in snippet and chunked modes
        next_id = 3
        if search_result is not None:
            for mode in ('snippet', 'chunked'):
                call_md = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "convert_to_markdown",
                        "arguments": {"structured": search_result, "options": {"mode": mode, "max_tokens": 200}}
                    },
                    "id": next_id,
                }
                print(f'Sending convert_to_markdown (mode={mode}) id={next_id} for search_debt_conversions result...')
                write_jsonrpc(proc, call_md)
                next_id += 1

            # Read responses for the markdown calls
            expected = list(range(3, next_id))
            print('Reading responses for convert_to_markdown (search) (timeout 45s)...')
            out_lines2, parsed2 = read_responses(proc, timeout=45, expected_ids=expected)
            for l in out_lines2:
                print(l)
            for p in parsed2:
                try:
                    print(json.dumps(p, indent=2))
                except Exception:
                    print(repr(p))

        # Now call get_recent_filings and repeat markdown conversion for that result
        call_grf = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_recent_filings",
                "arguments": {"ticker": "BYND", "form_type": "8-K", "count": 5}
            },
            "id": next_id,
        }
        print('Sending tool call get_recent_filings...')
        write_jsonrpc(proc, call_grf)
        expected_get_recent_id = next_id
        next_id += 1

        print('Reading responses for get_recent_filings (timeout 45s)...')
        out_lines3, parsed3 = read_responses(proc, timeout=45, expected_ids=[expected_get_recent_id])
        for l in out_lines3:
            print(l)
        for p in parsed3:
            try:
                print(json.dumps(p, indent=2))
            except Exception:
                print(repr(p))

        # Extract get_recent_filings result
        grf_result = None
        for p in parsed3:
            if isinstance(p, dict) and p.get('id') == expected_get_recent_id:
                grf_result = p.get('result')
                break

        if grf_result is not None:
            ids_for_grf = []
            for mode in ('snippet', 'chunked'):
                call_md = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "convert_to_markdown",
                        "arguments": {"structured": grf_result, "options": {"mode": mode, "max_tokens": 200}}
                    },
                    "id": next_id,
                }
                ids_for_grf.append(next_id)
                print(f'Sending convert_to_markdown (mode={mode}) id={next_id} for get_recent_filings result...')
                write_jsonrpc(proc, call_md)
                next_id += 1

            print('Reading responses for convert_to_markdown (get_recent_filings) (timeout 45s)...')
            out_lines4, parsed4 = read_responses(proc, timeout=45, expected_ids=ids_for_grf)
            for l in out_lines4:
                print(l)
            for p in parsed4:
                try:
                    print(json.dumps(p, indent=2))
                except Exception:
                    print(repr(p))
        else:
            print('No JSON responses parsed from stdout within timeout.')

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == '__main__':
    main()
