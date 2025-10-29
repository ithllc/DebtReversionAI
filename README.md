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
`Use stock ticker 'ATCH' and check the 52-week low and calculate MACD.`

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
│   ├── main.py           # UnifiedDebtReversionServer (all tools)
│   └── servers/
│       ├── edgar_server.py       # SEC filing tools
│       └── financial_server.py   # Stock data tools
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
│   └── test_dedalus.py
└── docs/                 # Detailed documentation
    ├── architecture.md
    ├── mcp_servers.md
    ├── setup.md
    └── testing.md
```
