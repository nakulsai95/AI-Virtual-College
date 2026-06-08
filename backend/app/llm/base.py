"""Provider interface shared by every LLM connector."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class ChatMessage(TypedDict):
    role: str  # "user" | "assistant"
    content: str


class LLMError(RuntimeError):
    """Raised when a provider call fails (bad key, network, etc.)."""


class LLMProvider(ABC):
    """A connected language-model backend.

    Concrete providers wrap a vendor SDK. They are constructed from the user's
    saved connector config (provider id + api key + model + optional base url).
    """

    id: str = "base"
    name: str = "Base"

    def __init__(self, api_key: str = "", model: str = "", base_url: str = ""):
        self.api_key = api_key or ""
        self.model = model or self.default_model
        self.base_url = base_url or ""

    @property
    def default_model(self) -> str:  # overridden per provider
        return ""

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 4000,
        json: bool = False,
    ) -> str:
        """Return the assistant's text for a single completion."""

    def test(self) -> dict:
        """Cheap round-trip to verify the connector works. Returns {ok, detail}."""
        try:
            out = self.complete(
                system="You are a connectivity check. Reply with the single word: pong.",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=16,
            )
            return {"ok": True, "detail": (out or "").strip()[:120] or "ok", "model": self.model}
        except LLMError as e:
            return {"ok": False, "detail": str(e)[:300], "model": self.model}
        except Exception as e:  # noqa: BLE001 - surface any SDK error to the user
            return {"ok": False, "detail": f"{type(e).__name__}: {e}"[:300], "model": self.model}
