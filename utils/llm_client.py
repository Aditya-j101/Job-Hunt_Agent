"""
Central wrapper for all Groq API calls.
Uses llama-3.1-8b-instant — free, fast, and reliable at structured JSON output.

The interface is kept identical to the previous Claude version:
call_claude_structured() is kept as the function name so resume_parser.py,
job_parser.py, and matcher.py need zero changes.
"""

import os
import re
import json
import time
import logging
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIConnectionError, APIError

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Add your Groq API key to your .env file."
    )

client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_client")

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2


def extract_json_from_response(text: str) -> dict:
    """
    Robustly extracts JSON from model output.
    LLMs sometimes wrap JSON in markdown code blocks or add commentary
    before/after — this handles all those cases cleanly.
    """
    # strip markdown code blocks if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.strip("`").strip()

    # try parsing the whole response first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # find the first {...} block in the response
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response:\n{text[:500]}")


def call_hf(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 0.1,
) -> str:
    """
    Basic text generation. Returns raw text response.
    """
    last_error = None
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency = time.time() - start_time
            result = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            logger.info(
                f"[call_Groq] model={model} attempt={attempt} "
                f"latency={latency:.2f}s total_tokens={tokens_used}"
            )
            return result

        except (RateLimitError, APIConnectionError, APIError) as e:
            last_error = e
            wait_time = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                f"[call_Groq] attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    logger.error(f"[call_Groq] all {MAX_RETRIES} attempts failed.")
    raise last_error


def call_Groq_structured(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    schema_name: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    **kwargs,
) -> dict:
    """
    Structured JSON extraction.
    Kept as call_claude_structured so no other file needs to change.
    """
    schema_str = json.dumps(schema, indent=2)
    structured_system = f"""{system_prompt}

CRITICAL INSTRUCTIONS:
- Respond with ONLY a valid JSON object, nothing else.
- Do not include any explanation, markdown, or text outside the JSON.
- Do not wrap the JSON in code blocks or backticks.
- The JSON must exactly match this schema for {schema_name}:
{schema_str}
- Do not add any fields not listed in the schema."""

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        try:
            raw_response = call_hf(
                system_prompt=structured_system,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=0.1,
            )
            latency = time.time() - start_time
            result = extract_json_from_response(raw_response)

            logger.info(
                f"[call_Groq_structured] schema={schema_name} "
                f"attempt={attempt} latency={latency:.2f}s"
            )
            return result

        except (ValueError, Exception) as e:
            last_error = e
            wait_time = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                f"[call_Groq_structured] attempt {attempt}/{MAX_RETRIES} "
                f"failed: {e}. Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    logger.error(f"[call_Groq_structured] all {MAX_RETRIES} attempts failed.")
    raise last_error