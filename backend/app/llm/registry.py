"""Provider catalogue + factory.

PROVIDER_SPECS is what the Connections UI renders: the list of connectors a
user can choose from, with the models each offers and where to get a key.
"""
from __future__ import annotations

from .base import LLMProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.mock_provider import MockProvider
from .providers.openai_compatible import (
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OllamaProvider,
    OpenAIProvider,
)

PROVIDER_SPECS: list[dict] = [
    {
        "id": "claude",
        "name": "Claude (Anthropic)",
        "tier": "strong reasoner",
        "requires_key": True,
        "default_model": "claude-opus-4-8",
        "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"],
        "key_url": "https://console.anthropic.com/settings/keys",
        "key_label": "ANTHROPIC_API_KEY",
    },
    {
        "id": "openai",
        "name": "OpenAI (GPT)",
        "tier": "balanced",
        "requires_key": True,
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
        "key_url": "https://platform.openai.com/api-keys",
        "key_label": "OPENAI_API_KEY",
    },
    {
        "id": "groq",
        "name": "Groq",
        "tier": "very fast",
        "requires_key": True,
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen-2.5-32b",
            "deepseek-r1-distill-llama-70b",
        ],
        "key_url": "https://console.groq.com/keys",
        "key_label": "GROQ_API_KEY",
    },
    {
        "id": "gemini",
        "name": "Gemini (Google)",
        "tier": "long-context",
        "requires_key": True,
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        "key_url": "https://aistudio.google.com/apikey",
        "key_label": "GEMINI_API_KEY",
    },
    {
        "id": "mistral",
        "name": "Mistral",
        "tier": "fast & open",
        "requires_key": True,
        "default_model": "mistral-large-latest",
        "models": [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "codestral-latest",
            "open-mistral-nemo",
        ],
        "key_url": "https://console.mistral.ai/api-keys",
        "key_label": "MISTRAL_API_KEY",
    },
    {
        "id": "ollama",
        "name": "Ollama (local)",
        "tier": "private · on-device",
        "requires_key": False,
        "default_model": "llama3.1",
        "models": ["llama3.1", "llama3.2", "mistral", "qwen2.5", "phi3"],
        "key_url": "https://ollama.com/download",
        "key_label": "(no key — runs locally)",
    },
]

_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "claude": AnthropicProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "mistral": MistralProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider,
}


def provider_spec(provider_id: str) -> dict | None:
    return next((s for s in PROVIDER_SPECS if s["id"] == provider_id), None)


def build_provider(config: dict | None) -> LLMProvider:
    """Construct the configured provider, falling back to the demo mock.

    Falls back when: no config, unknown provider, or a key-requiring provider
    with no key — so the app always has a working LLM to call.
    """
    if not config:
        return MockProvider()
    pid = config.get("provider", "")
    cls = _PROVIDER_CLASSES.get(pid)
    if cls is None:
        return MockProvider()
    spec = provider_spec(pid)
    if spec and spec["requires_key"] and not config.get("api_key"):
        return MockProvider()
    return cls(
        api_key=config.get("api_key", ""),
        model=config.get("model", ""),
        base_url=config.get("base_url", ""),
    )
