"""
Central wrapper for all Claude API calls.

Every node in graph/nodes.py, plus resume_parser.py and embeddings.py
(if it needs LLM-based reasoning alongside similarity scores), should
import call_claude() from here instead of talking to the Anthropic
client directly. This is the one file that owns the API key,
retry/backoff logic, and usage logging.
"""

import os
import time
import logging
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not found. Did you create a .env file "
        "(copied from .env.example) with your real key in it?"
    )

client = Anthropic(api_key=API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_client")

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2  # doubles each retry: 2s, 4s, 8s


def call_claude(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """
    Calls Claude with retry/backoff on transient errors (rate limits,
    connection issues, server errors), and logs latency + token usage
    for every call so you can track cost and performance across a
    full pipeline run.

    Raises the last error if all retries are exhausted, so callers
    can decide how to handle a hard failure (e.g. skip that job,
    add it to state["errors"]).
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            latency = time.time() - start_time
            usage = response.usage

            logger.info(
                f"[call_claude] model={model} attempt={attempt} "
                f"latency={latency:.2f}s input_tokens={usage.input_tokens} "
                f"output_tokens={usage.output_tokens}"
            )

            return response.content[0].text

        except (RateLimitError, APIConnectionError, APIError) as e:
            last_error = e
            wait_time = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                f"[call_claude] attempt {attempt}/{MAX_RETRIES} failed "
                f"({type(e).__name__}: {e}). Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    logger.error(f"[call_claude] all {MAX_RETRIES} attempts failed.")
    raise last_error

def call_claude_structured(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    schema_name: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
) -> dict:
    """
    Forces Claude to return output matching the given JSON schema using
    tool-use, instead of hoping a plain-text response parses as JSON.
    """
    tool = {
        "name": schema_name,
        "description": f"Extract structured data matching the {schema_name} schema.",
        "input_schema": schema,
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool],
                tool_choice={"type": "tool", "name": schema_name},
            )
            latency = time.time() - start_time
            usage = response.usage
            logger.info(
                f"[call_claude_structured] model={model} attempt={attempt} "
                f"latency={latency:.2f}s input_tokens={usage.input_tokens} "
                f"output_tokens={usage.output_tokens}"
            )

            for block in response.content:
                if block.type == "tool_use":
                    return block.input

            raise ValueError("No tool_use block found in response")

        except (RateLimitError, APIConnectionError, APIError) as e:
            last_error = e
            wait_time = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                f"[call_claude_structured] attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    logger.error(f"[call_claude_structured] all {MAX_RETRIES} attempts failed.")
    raise last_error