# Architecture

The DebtReversionAI application follows a multi-layer architecture designed for autonomous operation and clear separation of concerns.

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
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Financial Data│  │  EDGAR Data  │  │  AI Browser  │      │
│  │  MCP Server  │  │  MCP Server  │  │ (Manus AI)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
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

## Layers

1.  **User Interface Layer:** Handles interaction with the user via text (`interface/chat.py`) and voice (`interface/voice.py`). Voice capabilities are provided by Manus AI. The agent can also be run directly from `agent_runner.py`.

2.  **AI Agent Orchestration Layer:** This is the core of the application, located in `agents/`. The `StockAnalysisAgent` uses the `DedalusRunner` to orchestrate calls to different models (like Gemini) and tools.

3.  **MCP Server Layer:** A unified tool server deployed on the Dedalus Labs platform. The code for the server is in `src/`. The server uses an entry point wrapper (`main.py`) that launches the unified MCP server (`src/main.py`) via stdio transport.
    *   `src/main.py`: UnifiedDebtReversionServer that combines all tools
    *   `src/servers/financial_server.py`: Wraps `yfinance` and `pandas-ta` for stock data analysis
    *   `src/servers/edgar_server.py`: Wraps `edgartools` for searching SEC filings
    *   **Manus AI Browser:** Acts as a third tool server for web scraping and autonomous browsing tasks, like verifying options availability

4.  **Data Source Layer:** These are the external libraries and services that provide the raw data, including `yfinance`, `edgartools`, and various financial websites.

## Entry Point Architecture

The project uses a **wrapper entry point pattern** for Dedalus deployment:

```
main.py (Entry Point Wrapper)
    ↓
imports and launches
    ↓
src/main.py (UnifiedDebtReversionServer)
    ↓
stdio transport (Model Context Protocol)
```

This ensures the MCP server (not the agent) runs when deployed to Dedalus Labs.
