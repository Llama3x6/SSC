# llm.py
import os

import requests


def call_llm(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini")

    if provider == "anthropic":
        return _call_anthropic(prompt)
    elif provider == "gemini":
        return _call_gemini(prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'")


def _call_anthropic(prompt: str) -> str:
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
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


def _call_gemini(prompt: str) -> str:
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
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
