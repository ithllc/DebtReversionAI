import os
import asyncio
from openai import OpenAI


class ManusBrowser:
    def __init__(self):
        # Resolve the Manus API key from several possible environment variable names.
        # The hackathon contributors sometimes used a project-specific name like
        # 'aitinkerers10252025' instead of the generic 'MANUS_API_KEY'. Try a few
        # common variants so the wrapper works regardless of which one is present.
        possible_vars = [
            "MANUS_API_KEY",
            "MANUS_API_KEY_VALUE",
            "aitinkerers10252025",
            "AITINKERERS10252025",
            "MANUS_KEY",
        ]
        api_key = None
        for vn in possible_vars:
            v = os.getenv(vn)
            if v:
                api_key = v
                # store which env var we used for diagnostics
                self._manus_env_var = vn
                break

        if not api_key:
            # No key found - don't attempt to call the service with a malformed/empty token.
            # Keep the client None so callers can detect missing configuration.
            import logging

            logging.getLogger(__name__).warning(
                "Manus API key not found in environment. Looked for: %s",
                ",".join(possible_vars),
            )
            self.client = None
            return

        # Construct the OpenAI-compatible client pointed at Manus' v1 endpoint.
        self.client = OpenAI(base_url="https://api.manus.im/v1", api_key=api_key)

    async def _run_task(
        self, prompt: str, task_mode: str = "agent", agent_profile: str = "quality"
    ) -> str:
        """Creates a task, polls for completion, and returns the final message."""

        # The OpenAI SDK v1.100.2's .create() is synchronous, so we run it in a thread.
        def create_task():
            return self.client.responses.create(
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    }
                ],
                extra_body={
                    "task_mode": task_mode,
                    "agent_profile": agent_profile,
                },
            )

        response = await asyncio.to_thread(create_task)
        task_id = response.id

        # Polling loop
        while True:
            await asyncio.sleep(5)  # Wait 5 seconds between checks

            def retrieve_task():
                return self.client.responses.retrieve(response_id=task_id)

            task_update = await asyncio.to_thread(retrieve_task)

            if task_update.status in ["completed", "error", "pending"]:
                # 'pending' means it's waiting for user input, which we can't provide here.
                # We'll treat it as a final state for this simple wrapper.
                # The actual result is in the 'output' field which is a list of messages.
                if task_update.output:
                    # Find the last assistant message
                    for message in reversed(task_update.output):
                        if message.get("role") == "assistant":
                            content = message.get("content", [])
                            for part in content:
                                if part.get("type") == "text":
                                    return part.get("text", "")
                return f"Task finished with status: {task_update.status}"

    async def verify_options(self, ticker: str) -> str:
        """Use Manus AI to verify options availability."""
        prompt = f"Navigate to Yahoo Finance and verify if {ticker} has options available. Respond with only 'YES' or 'NO'."
        return await self._run_task(prompt)

    async def search_financial_news(self, ticker: str, topic: str) -> str:
        """Use Manus AI to search for financial news."""
        prompt = (
            f"Search for news about {ticker} related to {topic} and provide a summary."
        )
        return await self._run_task(prompt)

    async def extract_options_data(self, ticker: str) -> str:
        """Extract options chain data using Manus AI vision."""
        # The 'vision' mode is not explicitly in the API doc, but we can imply it by the prompt.
        prompt = f"Go to the Yahoo Finance options page for {ticker}, look at the screen, and extract the full options chain data as a JSON object."
        return await self._run_task(prompt, agent_profile="quality")
