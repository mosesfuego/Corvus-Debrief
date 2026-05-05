"""Tests for ranked LLM provider routing."""

import os
import sys

_THIS_FILE = os.path.abspath(__file__)
_TESTS_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_AGENT_ROOT, "src")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _SRC_DIR)

from llm.provider_router import get_ranked_providers, has_available_provider


def test_ranked_providers_use_config_order_and_skip_missing_keys():
    config = {
        "llm_providers": [
            {
                "name": "fallback",
                "rank": 2,
                "model": "fallback-model",
                "api_key": "fallback-key",
                "base_url": "https://fallback.example/v1",
            },
            {
                "name": "primary",
                "rank": 1,
                "model": "primary-model",
                "api_key": "primary-key",
                "base_url": "https://primary.example/v1",
            },
            {
                "name": "missing",
                "rank": 0,
                "model": "missing-model",
                "api_key": None,
            },
        ],
        "agents": {
            "provider": "legacy",
            "model": "legacy-model",
            "api_key": "legacy-key",
        },
    }

    providers = get_ranked_providers(config)

    assert [p["name"] for p in providers] == ["primary", "fallback"]
    assert has_available_provider(config)


def test_legacy_agent_config_is_used_when_no_ranked_list_exists():
    config = {
        "agents": {
            "provider": "legacy",
            "model": "legacy-model",
            "api_key": "legacy-key",
            "base_url": "https://legacy.example/v1",
        }
    }

    providers = get_ranked_providers(config)

    assert len(providers) == 1
    assert providers[0]["name"] == "legacy"


def test_gemini_can_rank_ahead_of_paid_fallbacks():
    config = {
        "llm_providers": [
            {
                "name": "moonshot_kimi",
                "rank": 2,
                "model": "kimi-k2.6",
                "api_key": "moonshot-key",
            },
            {
                "name": "google_gemini",
                "rank": 1,
                "model": "gemini-2.5-flash",
                "api_key": "gemini-key",
            },
            {
                "name": "nvidia_nim",
                "rank": 3,
                "model": "moonshotai/kimi-k2.6",
                "api_key": "nim-key",
            },
        ]
    }

    providers = get_ranked_providers(config)

    assert [p["name"] for p in providers] == [
        "google_gemini",
        "moonshot_kimi",
        "nvidia_nim",
    ]
