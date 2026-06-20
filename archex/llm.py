"""Multi-provider LLM client. Provider + model come from the profile's `llm:`
block; API keys come from env vars only (never the profile, never the repo).

OpenAI-compatible providers (groq / openai / ollama) share one code path.
Anthropic uses its native messages API.
"""
from __future__ import annotations

import json
import os
import time

import requests

from .util import extract_first_json_object, remove_trailing_commas, strip_json_fence

# provider -> (base_url, api_key_env). api_key_env None == no auth (local ollama)
PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "ollama": ("http://localhost:11434/v1", None),
    "anthropic": ("https://api.anthropic.com/v1", "ANTHROPIC_API_KEY"),
}


class LLMError(Exception):
    pass


def _api_key(cfg: dict, default_env: str | None) -> str | None:
    env = cfg.get("api_key_env", default_env)
    if not env:
        return None
    key = os.environ.get(env)
    if not key:
        raise LLMError(f"Missing API key: set ${env} in the environment")
    return key


def _post_with_retry(url, headers, body, max_retries=5, timeout=180):
    r = None
    for attempt in range(max_retries):
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code == 429:
            wait = min(30 * (2**attempt), 120)
            print(f"  rate limit, waiting {wait}s ({attempt + 1}/{max_retries})", flush=True)
            time.sleep(wait)
            continue
        break
    return r


def _chat_openai_compat(cfg, system, user, base_url):
    key = _api_key(cfg, PROVIDERS[cfg["provider"]][1])
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": cfg.get("max_tokens", 8192),
    }
    base = cfg.get("base_url", base_url)
    r = _post_with_retry(f"{base}/chat/completions", headers, body)
    if r.status_code != 200:
        raise LLMError(f"{cfg['provider']} API {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"]


def _chat_anthropic(cfg, system, user):
    key = _api_key(cfg, "ANTHROPIC_API_KEY")
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": cfg["model"],
        "max_tokens": cfg.get("max_tokens", 8192),
        "temperature": cfg.get("temperature", 0.3),
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    base = cfg.get("base_url", PROVIDERS["anthropic"][0])
    r = _post_with_retry(f"{base}/messages", headers, body)
    if r.status_code != 200:
        raise LLMError(f"anthropic API {r.status_code}: {r.text[:200]}")
    return r.json()["content"][0]["text"]


def chat(cfg: dict, system: str, user: str) -> str:
    provider = cfg.get("provider", "groq")
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider '{provider}' (have: {list(PROVIDERS)})")
    if provider == "anthropic":
        return _chat_anthropic(cfg, system, user)
    return _chat_openai_compat(cfg, system, user, PROVIDERS[provider][0])


def chat_json(cfg: dict, system: str, user: str) -> dict:
    """Call the model and parse a single JSON object out of the reply."""
    content = chat(cfg, system, user)
    content = strip_json_fence(content)
    obj = extract_first_json_object(content)
    if obj is None:
        raise LLMError(f"No JSON object in model reply: {content[:300]}")
    try:
        return json.loads(remove_trailing_commas(obj))
    except json.JSONDecodeError as e:
        raise LLMError(f"JSON parse error: {e} :: {obj[:400]}") from e
