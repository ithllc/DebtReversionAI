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

The MCP servers are defined in the `src/servers/` directory and launched by the main `src/main.py` entrypoint, as required by the Dedalus Labs deployment platform.

### Deployment from GitHub

The Dedalus Labs platform is designed to deploy Python servers directly from a GitHub repository.

1.  **Connect Your Repository:** In the Dedalus dashboard, connect your GitHub account and select the `DebtReversionAI` repository.
2.  **Configure Build Settings:**
    *   **Branch:** `main`
    *   **Build Type:** The platform should automatically detect a Python project. It will look for the required `src/main.py` file.
3.  **Configure Run Settings:**
    *   **Start Command:** The platform will automatically run `python src/main.py`.
    *   **Ports:** Expose ports `8000` and `8001` for the Edgar and Financial Data servers, respectively.
    *   **Environment Variables:** Add your `SEC_API_USER_AGENT` to the environment variables section in the Dedalus UI.

### Local Deployment using Docker

The easiest way to run the MCP servers locally is to use the provided `Dockerfile`.

1.  **Build the Docker image:**

    ```bash
    docker build -t debt-reversion-mcp .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d -p 8000:8000 -p 8001:8001 --env-file .env debt-reversion-mcp
    ```

This will start both the Edgar and Financial Data servers in a single container, accessible on `localhost:8000` and `localhost:8001`.

**These servers must be running (either locally or deployed) for the agent's tools to function correctly.**

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
