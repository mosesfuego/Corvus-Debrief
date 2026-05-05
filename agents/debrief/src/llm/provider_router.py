"""Ranked OpenAI-compatible provider routing."""

import os
from copy import deepcopy

from openai import OpenAI


class LLMProviderUnavailable(RuntimeError):
    """Raised when no configured LLM provider can serve a request."""


def _env_value(provider: dict) -> str | None:
    key_env = provider.get("api_key_env")
    if key_env:
        return os.environ.get(key_env)
    return None


def _with_resolved_key(provider: dict) -> dict:
    resolved = dict(provider)
    resolved["api_key"] = provider.get("api_key") or _env_value(provider)
    return resolved


def get_ranked_providers(config: dict) -> list[dict]:
    """Return configured providers with usable API keys, sorted by rank."""
    configured_providers = config.get("llm_providers", [])
    providers = [
        _with_resolved_key(provider)
        for provider in configured_providers
    ]

    legacy = config.get("agents", {})
    if not configured_providers and legacy.get("api_key"):
        providers.append({
            "name": legacy.get("provider", "legacy"),
            "rank": legacy.get("rank", 999),
            "model": legacy.get("model"),
            "api_key": legacy.get("api_key"),
            "base_url": legacy.get("base_url"),
            "extra_body": legacy.get("extra_body", {}),
        })

    usable = [
        provider for provider in providers
        if provider.get("api_key") and provider.get("model")
    ]
    return sorted(usable, key=lambda p: (p.get("rank", 999), p.get("name", "")))


def has_available_provider(config: dict) -> bool:
    """Return True when at least one ranked provider has a usable key."""
    return bool(get_ranked_providers(config))


def _merge_extra_body(request: dict, provider: dict) -> dict:
    merged = deepcopy(request)
    provider_extra = provider.get("extra_body") or {}
    request_extra = merged.get("extra_body") or {}
    if provider_extra or request_extra:
        merged["extra_body"] = {**provider_extra, **request_extra}
    return merged


def chat_completion_with_fallback(config: dict, request: dict):
    """Call ranked providers until one succeeds."""
    errors = []
    providers = get_ranked_providers(config)
    if not providers:
        raise LLMProviderUnavailable("No LLM providers have configured API keys.")

    for provider in providers:
        call = _merge_extra_body(request, provider)
        call["model"] = provider["model"]
        client = OpenAI(
            api_key=provider["api_key"],
            base_url=provider.get("base_url"),
        )
        try:
            print(
                "[CORVUS] LLM provider: "
                f"{provider.get('name', 'unnamed')} ({provider['model']})"
            )
            return client.chat.completions.create(**call)
        except Exception as exc:
            errors.append(
                f"{provider.get('name', 'unnamed')}:{provider.get('model')} "
                f"failed with {type(exc).__name__}: {exc}"
            )
            print(
                "[CORVUS] LLM provider failed: "
                f"{provider.get('name', 'unnamed')} ({type(exc).__name__})"
            )

    raise LLMProviderUnavailable(" | ".join(errors))
