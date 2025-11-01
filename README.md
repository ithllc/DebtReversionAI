# DebtReversionAI

> Proof-of-Concept for an autonomous FinTech AI agent that discovers high-probability mean reversion trades by analyzing stocks at 52-week lows with recent debt conversions—turning SEC filings and market technicals into actionable opportunities through conversational intelligence. Do not use for financial advice, educational tool only.

---

## 🎯 Project Overview

DebtReversionAI is an autonomous AI agent that identifies high-potential mean reversion trading opportunities. It combines:
- Stock financial data (52-week lows, MACD indicators)
- SEC EDGAR filings (debt conversions)
- AI-powered browser automation
- A conversational interface (text and voice)

The agent is orchestrated using the Dedalus Labs platform, with Anthropic Claude Sonnet 4 as the core reasoning model.

## 🏗️ Architecture

The application follows a multi-layer architecture designed for autonomous operation and clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                   USER INTERFACE LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Voice Input  │  │  Text Chat   │  │ Voice Output │      │
│  │  (Manus AI)  │  │   Interface  │  │ (Manus AI)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 AI AGENT ORCHESTRATION LAYER                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         LLM Agent (Gemini + Dedalus Runner)          │   │
│  │  - Natural language understanding                    │   │
│  │  - Tool orchestration & multi-model handoffs         │   │
│  │  - Decision making                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVER LAYER (Dedalus)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Unified DebtReversionAI MCP Server (stdio)        │   │
│  │  - Financial tools (yfinance, pandas-ta)             │   │
│  │  - EDGAR tools (edgartools)                          │   │
│  │  - Deployed as: ficonnectme2anymcp/DebtReversionAI   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────┐                                           │
│  │  AI Browser  │                                           │
│  │ (Manus AI)   │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       DATA SOURCE LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Yahoo Finance │  │   SEC EDGAR  │  │Options Chain │      │
│  │   (yfinance) │  │ (edgartools) │  │   Websites   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Technical Stack

- **Python 3.10+**
- **Orchestration:** [Dedalus Labs](https://www.dedaluslabs.ai/) for the MCP gateway and agent orchestration.
- **AI Browser:** [Manus AI](https://manus.im/) for browser automation, using the `openai` library as a client.
- **LLM:** Anthropic Claude Sonnet-4 (via Dedalus).
- **Financial Data:** `yfinance` for stock prices and `pandas-ta` for technical indicators.
- **SEC Filings:** `edgartools` for accessing the EDGAR database.
- **HTML→Markdown (optional):** `html2text` — improves conversion quality used by `src/tools/markdown_tools.py` when installed.

---

Refactor notes (committed)
--------------------------
The repository has been refactored and the following structural and functional
changes have been made and committed:

- Tools reorganized to `src/tools/`:
    - `src/tools/financial_tools.py` — yfinance helpers: `get_stock_data`, `get_stock_data_range`, `calculate_macd`, `check_52week_low`, `check_optionable`.
    - `src/tools/edgar_tools.py` — EDGAR helpers: `search_debt_conversions`, `get_recent_filings`, and helper utilities for parsing filing text and extracting price candidates.
    - `src/tools/markdown_tools.py` — `render_structured_result(structured: dict, options: dict) -> dict` for HTML→Markdown conversion and paragraph-based chunking.

- MCP server updates (`src/main.py`):
    - `src/main.py` now imports and uses the `src/tools/*` helpers directly.
    - New MCP tool exposed: `convert_to_markdown(structured: dict, options: dict = None) -> dict`, returning either a single markdown snippet (`{'mode':'snippet','markdown':...}`) or paragraph chunks (`{'mode':'chunked','chunks':[...]}`).

- Tests and utilities:
    - Added `tests/mcp_tool_tests/` with helpers to exercise streamable-HTTP and STDIO flows (`run_http_test.py`, `run_stdio_test.py`, `tools_streamable_client.py`, `tools_test_bynd_exact.py`) and unit tests for the markdown renderer.

- Dependency metadata:
    - `html2text` is listed as an optional dependency (see `requirements.txt` and `pyproject.toml`) and is used by `markdown_tools.py` for improved HTML→Markdown rendering when installed.

- Miscellaneous:
    - `src/main.py.bak` (backup of the pre-refactor entrypoint) is present in the tree for reference.
    - `test_results.md` was removed from the repository (outdated test artifact).

These changes are reflected in the project structure below and in the code under `src/` and `tests/`.

---

## 🚀 Getting Started

Follow these steps to set up and run the project.

### 1. Create a Python Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Navigate to the project directory
cd DebtReversionAI

# Create a virtual environment named 'aitinkerersdebtreversion'
python3 -m venv aitinkerersdebtreversion

# Activate the virtual environment
# On macOS and Linux:
source aitinkerersdebtreversion/bin/activate

# On Windows (PowerShell):
# .\aitinkerersdebtreversion\Scripts\Activate.ps1
```

### 2. Install Dependencies

This project has dependencies from PyPI and also uses a local version of the `pandas-ta` library.

```bash
# 1. Install pandas-ta from the local source directory
pip install -e ../pandas-ta/

# 2. Install the runtime dependencies
pip install -r requirements.txt

# 3. (Optional) Install the development dependencies (for linting/formatting)
pip install -r requirements-dev.txt
```

### 3. Configure API Keys

The agent requires API keys for Dedalus Labs and Manus AI, as well as an identity for the SEC EDGAR API.

1.  Copy the `.env.example` file to `.env` (or create it manually).
2.  Sign up for the required services:
    *   **Dedalus Labs:** [Ultimate Agents Hackathon](https://www.dedaluslabs.ai/ultimate-agents-hackathon)
    *   **Manus AI:** [AI Tinkerers NY Live Event](https://manus.im/live-events/AITinkerersNY)
3.  Add your keys and a user agent email to the `.env` file:

```env
# .env

# Dedalus Labs API Key
DEDALUS_API_KEY=your_dedalus_key_here

# Manus AI API Key
MANUS_API_KEY=your_manus_key_here

# SEC EDGAR Identity (your email is sufficient)
SEC_API_USER_AGENT=your.email@example.com
```

### 4. Deploy MCP Server

The MCP server is defined in `src/main.py` with an entry point wrapper in `main.py` for Dedalus deployment.

The unified server exposes all financial and SEC data tools to the agent. **The application will not be fully functional until this server is deployed to Dedalus Labs as `ficonnectme2anymcp/DebtReversionAI`**, as the agent relies on it to perform its core tasks.

**Deployment Requirements:**
- Set environment variable: `SEC_API_USER_AGENT=your.email@example.com` in Dedalus UI
- Server uses stdio transport (not HTTP ports) for Model Context Protocol
- Entry point: `main.py` wrapper → `src/main.py` unified server

See the [Setup Guide](docs/setup.md) for detailed deployment instructions.

### 5. Run the Agent

Once the setup is complete and the MCP server is deployed, you can start the agent chat interface:

```bash
python agent_runner.py
```

You can now interact with the DebtReversionAI agent from your terminal.

**Example Prompt:**
`Tell me about stock ticker "ETHZ" and did they do a debt conversion within the last 3 months?`

**To test the MCP server locally** (for debugging):
```bash
export SEC_API_USER_AGENT="your.email@example.com"
python main.py
```

---

## 📁 Project Structure

```
DebtReversionAI/
├── .env                  # Local environment variables (API keys)
├── main.py               # Entry point wrapper for MCP server deployment
├── agent_runner.py       # Agent chat interface entry point
├── requirements.txt      # Project dependencies
├── pyproject.toml        # Modern Python project configuration
├── README.md             # This file
├── src/                  # Source code for unified MCP server
│   ├── main.py           # UnifiedDebtReversionServer (entrypoint; imports tools from `src/tools`)
│   ├── tools/            # Reusable tool implementations (financial, EDGAR, markdown)
│   │   ├── financial_tools.py
│   │   ├── edgar_tools.py
│   │   └── markdown_tools.py
│   └── servers/
│       ├── edgar_server.py       # SEC filing tools (original server wrappers)
│       └── financial_server.py   # Stock data tools (original server wrappers)
├── agents/               # Core agent logic and prompts
│   ├── dedalus_orchestrator.py   # StockAnalysisAgent
│   ├── manus_browser.py          # AI browser integration
│   └── prompts.py                # System prompts
├── interface/            # User interface (chat, voice)
│   ├── chat.py
│   └── voice.py
├── utils/                # Helper functions and utilities
├── tests/                # Test suite (pytest)
│   ├── test_financial.py
│   ├── test_edgar.py
│   ├── test_dedalus.py
│   └── mcp_tool_tests/    # streamable and stdio helpers, BYND exact-range scripts, markdown unit tests
└── docs/                 # Detailed documentation
    ├── architecture.md
    ├── mcp_servers.md
    ├── setup.md
    └── testing.md
```
