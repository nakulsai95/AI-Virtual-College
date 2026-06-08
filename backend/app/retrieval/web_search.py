"""General web/university/syllabus search via a Search API connector (Tavily).

Optional: needs a user-supplied key (config = {"provider": "tavily", "api_key": ...}).
Returns cited results — never scraped page bodies. Degrades to [] when absent.
"""
from __future__ import annotations


def search(query: str, config: dict | None, n: int = 4) -> list[dict]:
    if not config or not config.get("api_key"):
        return []
    provider = (config.get("provider") or "tavily").lower()
    if provider == "tavily":
        return _tavily(query, config["api_key"], n)
    return []


def _tavily(query: str, api_key: str, n: int) -> list[dict]:
    try:
        import httpx
        r = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": n,
                  "search_depth": "basic"},
            timeout=8.0,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:  # noqa: BLE001
        return []
    out = []
    for res in (data.get("results") or [])[:n]:
        if res.get("title") and res.get("url"):
            out.append({"title": res["title"], "url": res["url"],
                        "snippet": (res.get("content") or "")[:200],
                        "kind": "web", "source": "tavily"})
    return out
