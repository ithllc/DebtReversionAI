from dedalus_labs import Dedalus
# DedalusRunner isn't exported at the top-level in some SDK builds. Try importing
# the helper from the runner subpackage as a fallback. If it's not available,
# fall back to using the Dedalus client directly in the chat method.
try:
    # Preferred (if SDK exports it at top-level)
    from dedalus_labs import DedalusRunner  # type: ignore
except Exception:
    try:
        # Fallback: import from the runner implementation package
        from dedalus_labs.lib.runner import DedalusRunner  # type: ignore
    except Exception:
        DedalusRunner = None  # type: ignore
from dotenv import load_dotenv
import os
import asyncio
import logging
from .prompts import SYSTEM_PROMPT

load_dotenv()

# module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class StockAnalysisAgent:
    def __init__(self):
        self.client = Dedalus(
            api_key=os.getenv("DEDALUS_API_KEY"),
            timeout=480.0,  # Extend timeout to 480 seconds
        )
        # Instantiate DedalusRunner only if available. Some SDK installs do not
        # re-export DedalusRunner at the top-level; we handled that above.
        if DedalusRunner is not None:
            try:
                self.runner = DedalusRunner(self.client)
            except Exception:
                # If instantiation fails for any reason, fall back to None and
                # use the direct client path in `chat`.
                self.runner = None
        else:
            self.runner = None
        self.conversation_history = []
        # Startup preflight: list available Dedalus models for this API key and
        # cache a short list for operators/debugging. We log a short sample so
        # operators can quickly see what models are available to the account.
        self.available_models = []
        try:
            resp = self.client.models.list()
            models = getattr(resp, "data", None)
            ids = []
            if models:
                for m in models:
                    try:
                        # prefer pydantic v2 model_dump, fallback to dict
                        if hasattr(m, "model_dump"):
                            d = m.model_dump()
                        elif hasattr(m, "dict"):
                            d = m.dict()
                        elif isinstance(m, dict):
                            d = m
                        else:
                            d = getattr(m, "__dict__", None) or {}

                        if isinstance(d, dict) and d.get("id"):
                            ids.append(d.get("id"))
                        else:
                            # last resort: try attribute access
                            id_attr = getattr(m, "id", None)
                            if id_attr:
                                ids.append(id_attr)
                            else:
                                ids.append(repr(m))
                    except Exception:
                        ids.append(repr(m))

            self.available_models = ids
            logger.info("Dedalus preflight: found %d models; sample ids: %s", len(ids), ", ".join(ids[:8]))
        except Exception as e:
            logger.warning("Dedalus preflight: failed to list models: %s", e)

    async def chat(self, user_message: str):
        """Process user message and orchestrate tool calls via Dedalus"""
        # Use Dedalus Runner with MCP servers. Wrap the call in try/except so
        # missing models or other remote errors return a readable message
        # instead of crashing the chat loop.
        try:
            # Preferred model selection order. These IDs were discovered via
            # a Dedalus models.list() call and are prioritized here based on
            # user preference. You can override this by setting
            # the DEDALUS_MODEL_LIST environment variable (comma-separated).
            # Use exact model ids as returned by Dedalus' models.list() for
            # this account. The IDs below were discovered via a prior
            # `client.models.list()` call and reflect provider namespaces.
            # You can override the prioritized list with the
            # DEDALUS_MODEL_LIST environment variable (comma-separated).
            default_models = [
                # Groq Qwen 3 (32B) - groq namespace variant
                #"groq/qwen/qwen3-32b",
                # MoonshotAI / Kimi K2 instruct via Groq namespace
                #"groq/moonshotai/kimi-k2-instruct",
                # Cerebras-hosted GPT-OSS 120B
                #"cerebras/openai/gpt-oss-120b",
                # Cerebras Qwen 3 (32B) variant
                #"cerebras/qwen-3-32b",
                # PlayAI TTS model
                #"groq/playai-tts",
                # Fallback: Groq Whisper turbo
                #"groq/whisper-large-v3-turbo",
                # Proven fallbacks: Anthropic and OpenAI
                "anthropic/claude-sonnet-4-20250514",
                "anthropic/claude-3-5-sonnet-20240620",
                "openai/gpt-4.1",
            ]

            env_models = os.getenv("DEDALUS_MODEL_LIST")
            if env_models:
                model_list = [m.strip() for m in env_models.split(",") if m.strip()]
            else:
                model_list = default_models

            # If the environment variable provides a comma-separated list,
            # use that ordering. Otherwise use our default_models. Try each
            # model in order until one succeeds.
            last_err = None
            # Prefer candidates that exist in the Dedalus preflight listing
            # to avoid trying model ids the account cannot access.
            filtered = [m for m in model_list if m in self.available_models]
            if filtered:
                try_list = filtered
            else:
                # If the preflight didn't return matching ids, fall back to
                # trying the original list (some ids may be vendor-normalized)
                try_list = model_list

            for model_id in try_list:
                try:
                    # Use DedalusRunner when available (it orchestrates tools,
                    # guardrails, and multi-turn flows). Otherwise fall back to
                    # a simple single-call to the Dedalus client API.
                    if getattr(self, "runner", None) is not None:
                        result = await asyncio.to_thread(
                            self.runner.run,
                            input=user_message,
                            model=model_id,
                            mcp_servers=[
                                "ficonnectme2anymcp/DebtReversionAI",  # Private MCP servers hosted on Dedalus
                                "windsor/brave-search-mcp",  # Dedalus marketplace tool
                            ],
                            instructions=SYSTEM_PROMPT,
                            stream=False,
                        )

                        # If the runner returns fine, provide the output and which
                        # model succeeded.
                        return f"[model_used={model_id}]\n" + getattr(result, "final_output", str(result))
                    else:
                        # Fallback: direct client call (single-turn). Keep the
                        # same mcp_servers and instruction wrapping.
                        def _call_client():
                            return self.client.chat.completions.create(
                                model=model_id,
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": user_message},
                                ],
                                mcp_servers=[
                                    "ficonnectme2anymcp/DebtReversionAI",
                                    "windsor/brave-search-mcp",
                                ],
                            )

                        resp = await asyncio.to_thread(_call_client)

                        # Attempt to extract assistant text from the response in a
                        # best-effort, robust way.
                        text = None
                        try:
                            choices = getattr(resp, "choices", None) or (resp.get("choices") if isinstance(resp, dict) else None)
                            if choices:
                                choice = choices[0]
                                msg = getattr(choice, "message", None) or (choice.get("message") if isinstance(choice, dict) else None)
                                if msg:
                                    text = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)

                            if not text:
                                text = getattr(resp, "output", None) or getattr(resp, "final_output", None) or getattr(resp, "text", None)

                            if not text:
                                text = str(resp)
                        except Exception:
                            text = str(resp)

                        return f"[model_used={model_id}]\n" + text

                except Exception as e:
                    last_err = e
                    # If the error message indicates the model is missing or
                    # unauthorized, try the next candidate. Otherwise break
                    # and return the error.
                    s = str(e).lower()
                    if (
                        "model_not_found" in s
                        or "does not exist" in s
                        or "not found" in s
                        or "access" in s
                        or "forbidden" in s
                        or "403" in s
                    ):
                        # try next model
                        continue
                    else:
                        # non-retriable error - return immediately
                        err_text = (
                            "Error running the agent: "
                            + str(e)
                            + "\nPlease check your DEDALUS_API_KEY and configured model names."
                        )
                        return err_text

            # If we exhausted candidates, return the last error in a readable form.
            if last_err is not None:
                return (
                    "Error running the agent: "
                    + str(last_err)
                    + "\nTried models: "
                    + ",".join(model_list)
                    + "\nPlease check your DEDALUS_API_KEY and configured model names."
                )
            else:
                return "No models configured to try. Set DEDALUS_MODEL_LIST or update the orchestrator."

        except Exception as e:
            # Provide a helpful error message for the chat UI. Often the
            # dedalus runner will fail if configured models are unavailable
            # in the current environment (e.g. Vertex AI model not found).
            err_text = (
                "Error running the agent: "
                + str(e)
                + "\nPlease check your DEDALUS_API_KEY and configured model names."
            )
            return err_text
