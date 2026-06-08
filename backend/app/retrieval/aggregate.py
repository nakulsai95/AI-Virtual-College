"""Combine all retrieval sources into one cited, de-duplicated reading list."""
from __future__ import annotations

from . import arxiv, open_index, web_search


def gather(query: str, *, search_config: dict | None = None, n: int = 10) -> list[dict]:
    """Pull from open index (always), arXiv (papers), and web search (if keyed)."""
    results: list[dict] = []
    results += open_index.search(query, n=6)
    results += arxiv.search(query, n=3)
    results += web_search.search(query, search_config, n=4)

    seen, out = set(), []
    for r in results:
        url = r.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(r)
        if len(out) >= n:
            break
    return out
