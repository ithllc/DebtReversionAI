# Setup and Running the Application

## 1. Installation

First, create a virtual environment and install the required dependencies.

### Dependency Management (`pyproject.toml`)

This project uses a `pyproject.toml` file to manage its dependencies. This is the modern standard for Python projects and is recommended by the Dedalus Labs build system. While the platform can fall back to using a `requirements.txt` file, using `pyproject.toml` resolves warnings in the build process and ensures a more reliable and standardized setup.

To install all necessary dependencies, run:

```bash
pip install .
```

This command reads the `pyproject.toml` file and installs all the packages listed under `dependencies`.

### Manual Installation (Legacy)

If you prefer to install dependencies manually, you can use the `requirements.txt` file.

```bash
# Navigate to the project directory
cd DebtReversionAI

# Create a virtual environment
python3 -m venv aitinkerersdebtreversion

# Activate the virtual environment
source aitinkerersdebtreversion/bin/activate  # On Windows use `aitinkerersdebtreversion\Scripts\activate`

# Install runtime dependencies
pip install -r requirements.txt

# (Optional) Install development dependencies
pip install -r requirements-dev.txt
```

## 2. API Keys

You will need to sign up for API keys from the following services as outlined in the project plan:

*   **Dedalus Labs:** For agent and model orchestration.
*   **Manus AI:** For AI browser automation.

Once you have your keys, create a `.env` file in the root of the `DebtReversionAI` directory and add your keys:

```env
# .env

# Dedalus Labs API Key
DEDALUS_API_KEY=your_dedalus_key_here

# Manus AI API Key
MANUS_API_KEY=your_manus_key_here

# SEC EDGAR Identity (Your email is sufficient)
SEC_API_USER_AGENT=your.email@example.com
```

## 3. Deploying MCP Servers

The MCP server is defined in `src/main.py` and launched via an entry point wrapper in `main.py`, as required by the Dedalus Labs deployment platform.

### Deployment from GitHub

The Dedalus Labs platform is designed to deploy Python servers directly from a GitHub repository.

1.  **Connect Your Repository:** In the Dedalus dashboard, connect your GitHub account and select the `DebtReversionAI` repository.
2.  **Configure Build Settings:**
    *   **Branch:** `main`
    *   **Build Type:** The platform should automatically detect a Python project with `pyproject.toml`.
    *   **Entry Point:** The platform will execute `uv run main` which runs the `main:main` function defined in `pyproject.toml`
3.  **Configure Environment Variables:**
    *   **Required:** Add `SEC_API_USER_AGENT=your.email@example.com` to environment variables in the Dedalus UI
    *   **Optional:** Add `DEDALUS_MODEL_LIST` for model preference

The server uses **stdio transport** (not HTTP ports) for Model Context Protocol communication.

### Local Testing

To test the MCP server locally:

```bash
# Activate virtual environment
source aitinkerersdebtreversion/bin/activate

# Set required environment variable
export SEC_API_USER_AGENT="your.email@example.com"

# Run the server
python main.py
```

The server will start and display:
```
🚀 DebtReversionAI MCP Server - Entry Point Wrapper
Starting unified DebtReversionAI MCP server...
Available tools: get_stock_data, calculate_macd, check_52week_low, check_optionable, search_debt_conversions, get_recent_filings
```

The server waits for MCP protocol messages on stdin (it won't respond to terminal input).

**The server must be deployed to Dedalus Labs for the agent's tools to function correctly.**

## 3.5 Model configuration and selection

We discovered that Dedalus exposes a combined model list from multiple providers (OpenAI, Anthropic, Gemini, Groq, Cerebras, etc.). Model identifiers returned by Dedalus are provider namespaced (for example `gemini/gemini/gemini-1.5-pro-latest` or `groq/groq/qwen-3-32b`). If you see `NotFound` or `InternalServerError` when the agent runs, it's usually because the configured model id is not recognized by the provider for the requested API method.

Recommendations:

- Prefer setting an environment variable `DEDALUS_MODEL_LIST` with a comma-separated list of model ids you want the agent to try, in priority order. Example:

```env
DEDALUS_MODEL_LIST=groq/groq/qwen-3-32b,groq/groq/moonshotai/kimi-k2-instruct,cerebras/cerebras/openai/gpt-oss-120b
```

- Alternatively, update the orchestrator's default model list in `agents/dedalus_orchestrator.py` to match the exact ids returned by `client.models.list()`.

- A simple preflight check can be added to call `client.models.list()` on startup to validate available models for your API key and environment.

We updated the orchestrator's default model preference to include the following models (priority order):

1. groq/groq/qwen/qwen3-32b
2. groq/groq/moonshotai/kimi-k2-instruct
3. cerebras/cerebras/openai/gpt-oss-120b
4. cerebras/cerebras/qwen-3-32b
5. groq/groq/playai-tts
6. groq/groq/whisper-large-v3-turbo (fallback)

The orchestrator now performs a startup preflight (calls `client.models.list()`) and logs a short sample of model ids available to the configured `DEDALUS_API_KEY`. This helps quickly surface which provider-namespaced ids are accessible to your account.

See `agents/dedalus_orchestrator.py` for the implementation detail and how to override with `DEDALUS_MODEL_LIST`.

## 4. Running the Application

### Running the Agent Locally

Once the dependencies are installed and the `.env` file is configured, you can start the agent chat interface:

```bash
python agent_runner.py
```

This will start the application and you can begin interacting with the DebtReversionAI agent in your terminal.

**Note:** The agent will not be fully functional until the MCP server is deployed on Dedalus Labs as `ficonnectme2anymcp/DebtReversionAI`, since the agent relies on it to perform financial analysis and data retrieval tasks.

### Running the MCP Server Locally

To run the MCP server (for testing or development):

```bash
export SEC_API_USER_AGENT="your.email@example.com"
python main.py
```

The server uses stdio transport and waits for MCP protocol messages. Use this for debugging server startup issues before deployment.
