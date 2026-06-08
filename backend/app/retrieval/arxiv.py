"""Open-access papers via the arXiv API (keyless). Degrades to [] when offline."""
from __future__ import annotations

import xml.etree.ElementTree as ET

_NS = {"a": "http://www.w3.org/2005/Atom"}


def search(query: str, n: int = 3) -> list[dict]:
    try:
        import httpx
        url = "http://export.arxiv.org/api/query"
        params = {"search_query": f"all:{query}", "start": 0, "max_results": n}
        r = httpx.get(url, params=params, timeout=6.0)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception:  # noqa: BLE001 - network/parse failure -> no papers
        return []

    out = []
    for entry in root.findall("a:entry", _NS)[:n]:
        title = (entry.findtext("a:title", default="", namespaces=_NS) or "").strip()
        link = (entry.findtext("a:id", default="", namespaces=_NS) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=_NS) or "").strip()
        if title and link:
            out.append({"title": title, "url": link, "snippet": summary[:200],
                        "kind": "paper", "source": "arxiv"})
    return out
