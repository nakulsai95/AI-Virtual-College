"""Approximate per-token pricing so the credit budget means something.

Prices are USD per 1M tokens (input, output), matched by longest model-name
prefix. They drift as vendors reprice — treat the costs as estimates that keep
the budget honest, not as a billing system.
"""
from __future__ import annotations

PRICES: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-haiku": (1.0, 5.0),
    # OpenAI
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
    # Groq-hosted open models
    "llama-3.3-70b": (0.59, 0.79),
    "llama-3.1-8b": (0.05, 0.08),
    "qwen": (0.29, 0.39),
    "deepseek": (0.75, 0.99),
    # Mistral
    "mistral-large": (2.00, 6.00),
    "mistral-medium": (0.40, 2.00),
    "mistral-small": (0.10, 0.30),
    "codestral": (0.30, 0.90),
    "open-mistral-nemo": (0.15, 0.15),
    # Google
    "gemini-2.5-pro": (1.25, 10.0),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.0-flash": (0.10, 0.40),
}

_FREE_PROVIDERS = {"ollama", "mock"}
_DEFAULT = (1.0, 3.0)


def price_for(model: str) -> tuple[float, float]:
    model = (model or "").lower()
    best = ""
    for prefix in PRICES:
        if model.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    return PRICES[best] if best else _DEFAULT


def estimate_cost(provider_id: str, model: str, input_tokens: int, output_tokens: int) -> float:
    if provider_id in _FREE_PROVIDERS:
        return 0.0
    p_in, p_out = price_for(model)
    return (input_tokens * p_in + output_tokens * p_out) / 1_000_000


def cheapest_model(models: list[str]) -> str:
    """The cheapest model in a provider's catalogue (by blended price)."""
    if not models:
        return ""
    return min(models, key=lambda m: sum(price_for(m)))
