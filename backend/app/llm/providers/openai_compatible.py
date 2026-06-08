"""OpenAI-compatible connectors: OpenAI (GPT), Groq, and Ollama.

Groq and Ollama both speak the OpenAI Chat Completions API, so a single
implementation drives all three — only the base URL, key requirement, and
default model differ.
"""
from __future__ import annotations

from ..base import ChatMessage, LLMError, LLMProvider


class _OpenAICompatible(LLMProvider):
    #: Default endpoint; OpenAI itself uses the SDK default (base_url stays "").
    api_base: str = ""
    #: Placeholder key for keyless local servers (Ollama).
    key_optional: bool = False

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise LLMError("openai SDK not installed — run pip install openai") from e

        key = self.api_key or ("ollama" if self.key_optional else "")
        if not key:
            raise LLMError(f"No API key configured for {self.name}.")
        base = self.base_url or self.api_base or None
        return OpenAI(api_key=key, base_url=base)

    def complete(self, system, messages, *, max_tokens=4000, json=False):
        client = self._client()
        payload: list[dict] = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend({"role": m["role"], "content": m["content"]} for m in messages)

        kwargs: dict = {"model": self.model, "messages": payload, "max_tokens": max_tokens}
        if json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            # Some OpenAI-compatible servers reject response_format — retry once
            # without it, nudging the model toward JSON in the prompt instead.
            if json and "response_format" in kwargs:
                kwargs.pop("response_format")
                kwargs["messages"] = payload + [
                    {"role": "user", "content": "Return only a single JSON object, no prose."}
                ]
                try:
                    resp = client.chat.completions.create(**kwargs)
                except Exception as e2:  # noqa: BLE001
                    raise LLMError(str(e2)) from e2
            else:
                raise LLMError(str(e)) from e

        return (resp.choices[0].message.content or "").strip()


class OpenAIProvider(_OpenAICompatible):
    id = "openai"
    name = "OpenAI (GPT)"

    @property
    def default_model(self) -> str:
        return "gpt-4o"


class GroqProvider(_OpenAICompatible):
    id = "groq"
    name = "Groq"
    api_base = "https://api.groq.com/openai/v1"

    @property
    def default_model(self) -> str:
        return "llama-3.3-70b-versatile"


class OllamaProvider(_OpenAICompatible):
    id = "ollama"
    name = "Ollama (local)"
    api_base = "http://localhost:11434/v1"
    key_optional = True

    @property
    def default_model(self) -> str:
        return "llama3.1"
