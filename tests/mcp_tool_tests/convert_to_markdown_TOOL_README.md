# convert_to_markdown tool — summary and usage

This file documents the new `convert_to_markdown` MCP tool and the supporting
helper module implemented in `src/tools/markdown_tools.py`. Drop this into the
`tests/mcp_tool_tests` folder for easy reference while iterating on tests.

## Files added/modified

- `src/tools/markdown_tools.py` — new helper module
  - Public API: `render_structured_result(structured: dict, options: dict) -> dict`
  - Features:
    - Heuristic HTML detection: checks for `<html`, `<body`, `<div`, `<p`, `<br`.
    - Uses `html2text` when installed to convert HTML → Markdown-like text;
      falls back to a minimal tag stripper if `html2text` is unavailable.
    - Paragraph chunker: `_paragraph_chunks(text, target_chars)` — splits on
      double-newline paragraphs and accumulates paragraphs until reaching a
      target character size, then yields chunks.
    - Two output modes:
      - `mode='snippet'` (default): returns a single markdown string up to
        `max_tokens` (approximated as chars) as `{'mode':'snippet','markdown':..., 'chars':...}`.
      - `mode='chunked'`: returns `{'mode':'chunked','chunks':[{'index':i,'markdown':..., 'chars':...}, ...]}`.

- `src/main.py` — updated to expose MCP tool wrapper
  - New MCP tool: `convert_to_markdown(structured: dict, options: dict = None) -> dict`
    - Calls `render_structured_result(...)` and returns the dict to the caller.

## Typical LLM workflow

1. Call `search_debt_conversions(ticker, months_back)` (existing tool) → returns
   structured result with `snippet` fields and metadata.
2. If the LLM needs a compact human-friendly summary, call the MCP tool
   `convert_to_markdown` with options `{"mode":"snippet","max_tokens":1200}`.
3. If the LLM wants to iterate over the full text, call
   `convert_to_markdown` with `{"mode":"chunked","max_tokens":2000}` and
   iterate the returned `chunks`.

## Example: run locally in the project venv

Note: these commands are examples to run locally from your shell. Adjust paths
to your venv or environment as needed.

1) Optional: install `html2text` in the venv for better HTML→Markdown conversion

```bash
/llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/pip install html2text
```

2) Quick Python test (snippet mode)

```bash
PYTHONPATH=/llm_models_python_code_src/DebtReversionAI \
  /llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python - <<'PY'
import json
from src.tools.markdown_tools import render_structured_result
sample = {'structuredContent': {'result': 'This is a <b>test</b> snippet.\n\nSecond paragraph.'}}
print(json.dumps(render_structured_result(sample, {'mode':'snippet','max_tokens':200}), indent=2))
PY
```

3) Quick Python test (chunked mode)

```bash
PYTHONPATH=/llm_models_python_code_src/DebtReversionAI \
  /llm_models_python_code_src/DebtReversionAI/aitinkerersdebtreversion/bin/python - <<'PY'
import json
from src.tools.markdown_tools import render_structured_result
sample = {'structuredContent': {'result': 'This is a <b>test</b> snippet.\n\nSecond paragraph.'}}
print(json.dumps(render_structured_result(sample, {'mode':'chunked','max_tokens':50}), indent=2))
PY
```

## Notes & caveats

- The module uses a simple tokens→chars heuristic (tokens * 4). This is
  conservative; adjust multiplier if you'd like a different token budget.
- The chunker is paragraph-aware. If input has no paragraph boundaries it will
  still chunk, but boundaries may be less semantic.
- `html2text` is optional; install it in the venv for high-quality HTML
  conversion.

## Next steps (pick one when you continue)

- Run an STDIO JSON-RPC end-to-end test that: calls `search_debt_conversions`,
  then calls `convert_to_markdown` in both `snippet` and `chunked` modes and
  captures the responses.
- Add unit tests that mock EDGAR filing objects to validate parsing and
  chunking deterministically.

-- Paused here — will continue when you say so.
