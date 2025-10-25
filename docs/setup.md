# Setup and Running the Application

## 1. Installation

First, create a virtual environment and install the required dependencies.

```bash
# Navigate to the project directory
cd DebtReversionAI

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
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

The tool servers located in the `mcp_servers/` directory (`financial_server.py` and `edgar_server.py`) are designed to be deployed on the Dedalus Labs platform. The project plan states this can be done in a few clicks from a GitHub repository.

**These servers must be deployed and running on Dedalus for the agent's tools to function correctly.**

## 4. Running the Application

Once the dependencies are installed and the `.env` file is configured, you can start the chat interface:

```bash
python main.py
```

This will start the application and you can begin interacting with the DebtReversionAI agent in your terminal.

**Note:** The application will not be fully functional until the MCP servers are deployed on Dedalus Labs, as the agent relies on them to perform its financial analysis and data retrieval tasks.
