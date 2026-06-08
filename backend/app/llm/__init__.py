"""Provider-agnostic LLM layer for AULA.

Users pick a provider (Claude / OpenAI / Groq / Ollama) and supply their own
key in the UI; the agents call whichever one is connected. A mock provider is
used as a fallback so the whole app runs before any key is added.
"""
from .base import ChatMessage, LLMError, LLMProvider
from .registry import PROVIDER_SPECS, build_provider, provider_spec

__all__ = [
    "ChatMessage",
    "LLMError",
    "LLMProvider",
    "PROVIDER_SPECS",
    "build_provider",
    "provider_spec",
]
