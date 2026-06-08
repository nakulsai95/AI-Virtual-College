"""Claude (Anthropic) connector — uses the official anthropic SDK."""
from __future__ import annotations

from ..base import ChatMessage, LLMError, LLMProvider


class AnthropicProvider(LLMProvider):
    id = "claude"
    name = "Claude (Anthropic)"

    @property
    def default_model(self) -> str:
        return "claude-opus-4-8"

    def complete(self, system, messages, *, max_tokens=4000, json=False):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise LLMError("anthropic SDK not installed — run pip install anthropic") from e

        if not self.api_key:
            raise LLMError("No Anthropic API key configured.")

        if json:
            system = (system or "") + "\n\nRespond with a single valid JSON object and nothing else."

        client = anthropic.Anthropic(api_key=self.api_key)
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or None,
                thinking={"type": "adaptive"},
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            )
        except anthropic.APIError as e:
            raise LLMError(getattr(e, "message", None) or str(e)) from e

        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "".join(parts).strip()
