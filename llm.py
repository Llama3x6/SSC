# llm.py
import json
import os
from typing import Generic, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Pins the Anthropic request/response format. Required on every call; the API
# rejects requests without it.
ANTHROPIC_VERSION = "2023-06-01"


def _anthropic_model() -> str:
    """Model id for Anthropic calls, overridable without touching the code."""
    return os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


def _gemini_model() -> str:
    """Model id for Gemini calls, overridable without touching the code."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _gemini_url(model: str) -> str:
    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )


def _flatten_schema(schema: Type[T]) -> dict:
    """Return `schema`'s JSON Schema, shaped for structured-output requests.

    Pydantic emits `$defs` plus `$ref` for nested models. Neither Anthropic's
    `output_config.format` nor Gemini's `responseSchema` documents support for
    references, so definitions are inlined. `additionalProperties: false` is
    added to every object: Anthropic requires it, Gemini accepts it.
    """
    raw = schema.model_json_schema()
    definitions = raw.pop("$defs", {})
    return _inline_refs(raw, definitions, ())


def _inline_refs(node: object, definitions: dict, stack: tuple[str, ...]) -> object:
    """Recursively replace `$ref` nodes with their definition."""
    if isinstance(node, list):
        return [_inline_refs(item, definitions, stack) for item in node]
    if not isinstance(node, dict):
        return node

    ref = node.get("$ref")
    if ref is not None:
        name = ref.rsplit("/", 1)[-1]
        if name in stack:
            raise ValueError(
                f"Recursive schema '{name}' cannot be inlined for structured output"
            )
        if name not in definitions:
            raise ValueError(f"Unresolvable schema reference: {ref}")
        resolved = _inline_refs(definitions[name], definitions, stack + (name,))
        # Keys alongside a $ref (a description, say) override the definition.
        siblings = {
            key: _inline_refs(value, definitions, stack)
            for key, value in node.items()
            if key != "$ref"
        }
        return {**resolved, **siblings}

    out = {
        key: _inline_refs(value, definitions, stack)
        for key, value in node.items()
        if key != "$defs"
    }
    if out.get("type") == "object":
        out["additionalProperties"] = False
    return out


def _first_text_block(payload: dict) -> str:
    """Text of the first text block in an Anthropic response."""
    for block in payload.get("content", []):
        if block.get("type") == "text":
            return block.get("text", "")
    raise RuntimeError("Anthropic response contained no text block")


def call_llm(prompt: str) -> str:
    """Plain text LLM call — no structured output."""
    provider = os.getenv("LLM_PROVIDER", "gemini")

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
    LLM call with schema-constrained output.

    Both providers constrain generation server-side from the schema derived
    from `schema`, and the response is validated against the Pydantic model
    before being returned.

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
    provider = os.getenv("LLM_PROVIDER", "gemini")

    if provider == "anthropic":
        return _call_anthropic_structured(prompt, schema, max_retries)
    elif provider == "gemini":
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
                "anthropic-version": ANTHROPIC_VERSION,
            },
            json={
                "model": _anthropic_model(),
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
    Anthropic structured output via `output_config.format`.

    The schema is enforced server-side, so the response is already valid JSON
    of the right shape. The retry loop stays as a guard for the cases the API
    does not cover: Pydantic is stricter than the schema it sends, because
    constraint keywords are not part of the structured-output subset.
    """
    json_schema = _flatten_schema(schema)
    last_error: Exception | None = None

    for _ in range(max_retries):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    "anthropic-version": ANTHROPIC_VERSION,
                },
                json={
                    "model": _anthropic_model(),
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                    "output_config": {
                        "format": {"type": "json_schema", "schema": json_schema}
                    },
                },
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Anthropic API error: {e.response.status_code} — {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise RuntimeError(f"Anthropic request failed: {e}") from e

        payload = resp.json()
        stop_reason = payload.get("stop_reason")

        # Both are 200 responses whose body does not satisfy the schema, so
        # they have to be caught explicitly rather than left to validation.
        if stop_reason == "refusal":
            raise RuntimeError(
                "Anthropic declined to answer this prompt (stop_reason=refusal)"
            )
        if stop_reason == "max_tokens":
            raise RuntimeError(
                "Anthropic response hit the token limit and is truncated; "
                "raise max_tokens or shorten the prompt"
            )

        try:
            return schema.model_validate(json.loads(_first_text_block(payload)))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue

    raise RuntimeError(
        f"Anthropic structured output failed validation after {max_retries} "
        f"attempts: {last_error}"
    ) from last_error


def _call_gemini(prompt: str) -> str:
    """Plain text call to Gemini API."""
    try:
        resp = requests.post(
            _gemini_url(_gemini_model()),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": os.environ["GEMINI_API_KEY"],
            },
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
    Gemini structured output via `generationConfig.responseSchema`.

    Constrained server-side, same as the Anthropic path. The retry loop stays
    as a guard for anything Pydantic rejects that the sent schema could not
    express.
    """
    json_schema = _flatten_schema(schema)
    last_error: Exception | None = None

    for _ in range(max_retries):
        try:
            resp = requests.post(
                _gemini_url(_gemini_model()),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": os.environ["GEMINI_API_KEY"],
                },
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": json_schema,
                    },
                },
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Gemini API error: {e.response.status_code} — {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise RuntimeError(f"Gemini request failed: {e}") from e

        payload = resp.json()
        candidate = payload["candidates"][0]

        # A truncated candidate is a 200 whose JSON is cut mid-structure.
        if candidate.get("finishReason") == "MAX_TOKENS":
            raise RuntimeError(
                "Gemini response hit the token limit and is truncated; "
                "raise maxOutputTokens or shorten the prompt"
            )

        text = candidate["content"]["parts"][0]["text"]
        try:
            return schema.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue

    raise RuntimeError(
        f"Gemini structured output failed validation after {max_retries} "
        f"attempts: {last_error}"
    ) from last_error
