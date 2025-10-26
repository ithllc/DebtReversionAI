# Setup and Running the Application

## 1. Installation

First, create a virtual environment and install the required dependencies.

```bash
# Navigate to the project directory
cd DebtReversionAI

# Create a virtual environment
python3 -m venv aitinkerersdebtreversion

# Activate the virtual environment
source aitinkerersdebtreversion/bin/activate  # On Windows use `aitinkerersdebtreversion\Scripts\activate`

# Install local pandas-ta dependency
pip install -e ../pandas-ta/

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

The tool servers located in the `mcp_servers/` directory (`financial_server.py` and `edgar_server.py`) are designed to be deployed on the Dedalus Labs platform.

### Deployment using Docker

The easiest way to deploy the MCP servers is to use Docker. A `Dockerfile` is provided in the root of the project.

1.  **Build the Docker image:**

    ```bash
    docker build -t debt-reversion-mcp .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d -p 8000:8000 --env-file .env debt-reversion-mcp
    ```

This will start both the Edgar and Financial Data servers in a single container.

### Deployment to Dedalus Labs

The `dedalus-sdk-python` library provides a command-line interface for deploying services to Dedalus Labs. To deploy the MCP servers, you can use the `dedalus deploy` command.

1.  **Login to Dedalus Labs:**

    ```bash
    dedalus login
    ```

2.  **Deploy the servers:**

    You will need to create a deployment configuration file (e.g., `dedalus.yml`) to specify the servers to deploy.

    **`dedalus.yml`:**
    ```yaml
    services:
      - name: edgar-data
        path: mcp_servers/edgar_server.py
      - name: financial-data
        path: mcp_servers/financial_server.py
    ```

    Then, run the deploy command:

    ```bash
    dedalus deploy -f dedalus.yml
    ```

**These servers must be deployed and running on Dedalus for the agent's tools to function correctly.**

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

Once the dependencies are installed and the `.env` file is configured, you can start the chat interface:

```bash
python main.py
```

This will start the application and you can begin interacting with the DebtReversionAI agent in your terminal.

**Note:** The application will not be fully functional until the MCP servers are deployed on Dedalus Labs, as the agent relies on them to perform its financial analysis and data retrieval tasks.
