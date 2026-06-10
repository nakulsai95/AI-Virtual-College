"""Credit metering — every LLM call is budgeted, costed, and recorded.

Wrap any provider with metered(provider, agent_id) and:
  1. Calls are blocked once the credit cap is spent (BudgetExceeded — callers
     already degrade to the mock provider, so the app keeps working).
  2. When less than 25% of the budget remains, the call is downshifted to the
     provider's cheapest model so remaining credits stretch further.
  3. Token usage and estimated cost are recorded per agent (drives the
     Command Center budget bars and /api/usage).
"""
from __future__ import annotations

import logging

from .. import db
from .base import LLMError, LLMProvider
from .pricing import cheapest_model, estimate_cost
from .registry import provider_spec

log = logging.getLogger("aula.metering")

_DOWNSHIFT_AT = 0.25  # downshift when remaining budget falls below this fraction
_logged_downshifts: set[tuple[str, str]] = set()


class BudgetExceeded(LLMError):
    """Raised before a call when the credit budget is spent."""


class MeteredProvider(LLMProvider):
    """Wraps a real provider with budget enforcement + usage recording.

    tier="bulk" routes the call to the provider's cheapest model — used for
    high-volume content (the lesson factory, chat replies) so a full
    university catalog costs dollars, not tens of dollars. Design, validation,
    exams and the Provost stay on the user's main model (tier="main").
    """

    def __init__(self, inner: LLMProvider, agent: str, action: str = "",
                 tier: str = "main"):
        self._inner = inner
        self._agent = agent
        self._action = action
        if tier == "bulk" and inner.id not in ("mock", "ollama"):
            spec = provider_spec(inner.id)
            cheap = cheapest_model(spec["models"]) if spec else ""
            if cheap:
                inner.model = cheap
        self.id = inner.id
        self.name = inner.name
        self.api_key = inner.api_key
        self.base_url = inner.base_url
        self.model = inner.model
        self.last_usage = None

    @property
    def default_model(self) -> str:
        return self._inner.default_model

    def complete(self, system, messages, *, max_tokens=4000, json=False):
        if self.id != "mock":
            self._enforce_budget()
        out = self._inner.complete(system, messages, max_tokens=max_tokens, json=json)
        self._record(system, messages, out)
        return out

    def test(self) -> dict:
        return self._inner.test()

    # -- internals --------------------------------------------------------

    def _enforce_budget(self):
        cap = db.budget_cap()
        used = db.usage_total()
        if used >= cap:
            db.log_feed("system",
                        f"Credit budget spent (${cap:.2f}) — agents running in demo mode. "
                        "Raise the cap in Connections.", "neg")
            raise BudgetExceeded(
                f"Credit budget of ${cap:.2f} is spent (${used:.2f} used). "
                "Raise the cap to keep using the connected model.")
        # Budget-aware routing: low credits -> cheapest model the provider offers.
        if cap > 0 and (cap - used) / cap < _DOWNSHIFT_AT:
            spec = provider_spec(self.id)
            cheap = cheapest_model(spec["models"]) if spec else ""
            if cheap and cheap != self._inner.model:
                key = (self._agent, cheap)
                if key not in _logged_downshifts:
                    _logged_downshifts.add(key)
                    db.log_feed("system",
                                f"Budget low — {self._agent} downshifted to {cheap} "
                                "to stretch remaining credits.", "update")
                self._inner.model = cheap
                self.model = cheap

    def _record(self, system, messages, out):
        usage = getattr(self._inner, "last_usage", None)
        if not usage:
            # No vendor-reported counts — estimate at ~4 chars/token.
            sent = len(system or "") + sum(len(m.get("content", "")) for m in messages)
            usage = {"input_tokens": sent // 4, "output_tokens": len(out or "") // 4}
        self.last_usage = usage
        cost = estimate_cost(self.id, self._inner.model,
                             usage["input_tokens"], usage["output_tokens"])
        try:
            db.record_usage(self._agent, self.id, self._inner.model, self._action,
                            usage["input_tokens"], usage["output_tokens"], cost)
        except Exception:  # noqa: BLE001 - metering must never break a call
            log.exception("failed to record usage")


def metered(provider: LLMProvider, agent: str, action: str = "",
            tier: str = "main") -> LLMProvider:
    return MeteredProvider(provider, agent, action, tier)
