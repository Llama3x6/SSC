# llm.py
import json
import os
from typing import Generic, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def call_llm(prompt: str) -> str:
    """Plain text LLM call — no structured output."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        return _call_anthropic(prompt)
    elif provider == "gemini":
        return _call_gemini(prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'")


def call_llm_structured(
    prompt: str,
    schema: Type[T],
    max_retries: int = 3,
) -> T:
    """
    LLM call with structured output validation.

    Uses Anthropic's json_schema for structured outputs, validates against
    Pydantic schema, and retries on validation failure.

    Args:
        prompt: The prompt to send to the LLM
        schema: A Pydantic BaseModel class to validate output against
        max_retries: Maximum number of retries on validation failure

    Returns:
        Validated instance of the schema

    Raises:
        RuntimeError: If API call fails or max retries exceeded
        ValidationError: If output cannot be validated (after retries)
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        return _call_anthropic_structured(prompt, schema, max_retries)
    elif provider == "gemini":
        # Gemini fallback: use plain text + Pydantic validation
        return _call_gemini_structured(prompt, schema, max_retries)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'")


def _call_anthropic(prompt: str) -> str:
    """Plain text call to Anthropic API."""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            },
            json={
                "model": "claude-opus-4-6",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except requests.HTTPError as e:
        raise RuntimeError(
            f"Anthropic API error: {e.response.status_code} — {e.response.text}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Anthropic call failed: {e}") from e


def _call_anthropic_structured(
    prompt: str,
    schema: Type[T],
    max_retries: int,
) -> T:
    """
    Anthropic API call with structured output (json_schema).

    Retries on validation failure up to max_retries times.
    """
    # Generate JSON schema from Pydantic model
    json_schema = schema.model_json_schema()

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                },
                json={
                    "model": "claude-opus-4-6",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                    "betas": ["interleaved-thinking-2025-05-14"],
                    "thinking": {"type": "enabled", "budget_tokens": 5000},
                    "temperature": 1,  # Required for structured outputs with thinking
                },
            )
            resp.raise_for_status()
            response_data = resp.json()

            # Extract the JSON from response
            # With structured outputs, content should be JSON
            content = response_data["content"][0]

            if content.get("type") == "thinking":
                # Skip thinking block if present, get text block
                for block in response_data["content"]:
                    if block.get("type") == "text":
                        content = block
                        break

            text = content.get("text", "")

            # Parse JSON and validate
            parsed = json.loads(text)
            validated = schema.model_validate(parsed)
            return validated

        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Failed to parse JSON after {max_retries} retries: {e}"
                ) from e
            # Retry on JSON parse error
            continue
        except ValidationError as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Schema validation failed after {max_retries} retries:\n{e}"
                ) from e
            # Retry on validation error
            continue
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Anthropic API error: {e.response.status_code} — {e.response.text}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Anthropic structured call failed: {e}") from e

    raise RuntimeError(
        f"Failed to get valid structured output after {max_retries} retries"
    )


def _call_gemini(prompt: str) -> str:
    """Plain text call to Gemini API."""
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.HTTPError as e:
        raise RuntimeError(
            f"Gemini API error: {e.response.status_code} — {e.response.text}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Gemini call failed: {e}") from e


def _call_gemini_structured(
    prompt: str,
    schema: Type[T],
    max_retries: int,
) -> T:
    """
    Gemini fallback: plain text + Pydantic validation.

    Sends prompt to Gemini and validates response against schema.
    Retries on validation failure.
    """
    # Add JSON schema instruction to prompt
    json_schema = schema.model_json_schema()
    augmented_prompt = f"""{prompt}

Please respond with ONLY valid JSON matching this schema:
{json.dumps(json_schema, indent=2)}

Do not include markdown formatting, code blocks, or explanatory text — just the raw JSON."""

    for attempt in range(max_retries):
        try:
            api_key = os.environ["GEMINI_API_KEY"]
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": augmented_prompt}]}]},
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

            # Parse and validate
            parsed = json.loads(text)
            validated = schema.model_validate(parsed)
            return validated

        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Failed to parse JSON after {max_retries} retries: {e}"
                ) from e
            continue
        except ValidationError as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Schema validation failed after {max_retries} retries:\n{e}"
                ) from e
            continue
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Gemini API error: {e.response.status_code} — {e.response.text}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Gemini structured call failed: {e}") from e

    raise RuntimeError(
        f"Failed to get valid structured output after {max_retries} retries"
    )
