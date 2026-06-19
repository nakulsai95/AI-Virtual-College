"""Keyless web research for the agents.

The Principal uses this to study how real universities structure a topic
before designing the curriculum; Professors use it to stock the library with
books, papers, and articles. Four sources, none needing an API key:

  - DuckDuckGo (HTML endpoint)  — university syllabi / course pages
  - Wikipedia                   — topic overviews
  - arXiv                       — papers
  - Open Library                — books

Every call is time-boxed and failure-tolerant: no network (or AULA_NO_NET=1)
just means fewer sources, never an error.
"""
from __future__ import annotations

import html as html_lib
import logging
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET

import httpx

log = logging.getLogger("aula.research")

_TIMEOUT = httpx.Timeout(6.0)
_HEADERS = {"User-Agent": "AULA-virtual-college/1.0 (local research agent)"}


def _off() -> bool:
    return os.getenv("AULA_NO_NET", "") == "1"


def _get(url: str, **kwargs) -> httpx.Response | None:
    if _off():
        return None
    try:
        r = httpx.get(url, timeout=_TIMEOUT, headers=_HEADERS,
                      follow_redirects=True, **kwargs)
        return r if r.status_code == 200 else None
    except Exception:  # noqa: BLE001 - research is best-effort
        return None


# --- DuckDuckGo: web links (university curricula, course pages) -----------

def search_web(query: str, n: int = 5) -> list[dict]:
    """[{title, url}] from DuckDuckGo's HTML endpoint. Best-effort."""
    r = _get("https://html.duckduckgo.com/html/",
             params={"q": query})
    if r is None:
        return []
    out = []
    for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            r.text, re.DOTALL):
        url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        # DDG wraps results in a redirect: //duckduckgo.com/l/?uddg=<real-url>
        q = urllib.parse.urlparse(url).query
        real = urllib.parse.parse_qs(q).get("uddg", [url])[0]
        if title and real.startswith("http"):
            out.append({"title": title[:160], "url": real})
        if len(out) >= n:
            break
    return out


# --- Wikipedia: topic overview ---------------------------------------------

def wikipedia_summary(topic: str) -> dict | None:
    """{title, url, summary} for the closest Wikipedia article."""
    r = _get("https://en.wikipedia.org/w/api.php",
             params={"action": "opensearch", "search": topic, "limit": 1,
                     "namespace": 0, "format": "json"})
    if r is None:
        return None
    try:
        data = r.json()
        if not data[1]:
            return None
        title, url = data[1][0], data[3][0]
    except Exception:  # noqa: BLE001
        return None
    s = _get("https://en.wikipedia.org/api/rest_v1/page/summary/"
             + urllib.parse.quote(title))
    summary = ""
    if s is not None:
        try:
            summary = (s.json().get("extract") or "")[:900]
        except Exception:  # noqa: BLE001
            pass
    return {"title": title, "url": url, "summary": summary}


# --- full texts: the teaching corpus ----------------------------------------

def _mw_extract(api_host: str, title: str, cap: int) -> str:
    """Full plain-text extract of a MediaWiki page (Wikipedia/Wikibooks)."""
    r = _get(f"https://{api_host}/w/api.php",
             params={"action": "query", "prop": "extracts", "explaintext": 1,
                     "format": "json", "titles": title, "redirects": 1})
    if r is None:
        return ""
    try:
        pages = r.json()["query"]["pages"]
        return (next(iter(pages.values())).get("extract") or "")[:cap]
    except Exception:  # noqa: BLE001
        return ""


def wikipedia_full(topic: str, cap: int = 6000) -> list[dict]:
    """The FULL article text — thousands of words of real teaching content."""
    w = wikipedia_summary(topic)
    if not w:
        return []
    content = _mw_extract("en.wikipedia.org", w["title"], cap)
    return [{"title": w["title"] + " — full article", "url": w["url"],
             "authors": "Wikipedia", "summary": (content or w["summary"])[:300],
             "content": content}]


def wikibooks(topic: str, n: int = 2, cap: int = 5000) -> list[dict]:
    """Open textbooks from Wikibooks, with their actual text scraped."""
    r = _get("https://en.wikibooks.org/w/api.php",
             params={"action": "opensearch", "search": topic, "limit": n,
                     "namespace": 0, "format": "json"})
    if r is None:
        return []
    try:
        data = r.json()
        titles, urls = data[1], data[3]
    except Exception:  # noqa: BLE001
        return []
    out = []
    for title, url in zip(titles[:n], urls[:n]):
        content = _mw_extract("en.wikibooks.org", title, cap)
        out.append({"title": title, "url": url, "authors": "Wikibooks (open textbook)",
                    "summary": content[:300], "content": content})
    return out


# --- arXiv: papers -----------------------------------------------------------

def arxiv_papers(topic: str, n: int = 3) -> list[dict]:
    """[{title, authors, url, summary}] from the arXiv Atom API."""
    r = _get("http://export.arxiv.org/api/query",
             params={"search_query": f"all:{topic}", "start": 0,
                     "max_results": n, "sortBy": "relevance"})
    if r is None:
        return []
    out = []
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in ET.fromstring(r.text).findall("a:entry", ns):
            title = re.sub(r"\s+", " ", entry.findtext("a:title", "", ns)).strip()
            url = entry.findtext("a:id", "", ns).strip()
            authors = ", ".join(a.findtext("a:name", "", ns)
                                for a in entry.findall("a:author", ns)[:3])
            summary = re.sub(r"\s+", " ", entry.findtext("a:summary", "", ns)).strip()[:300]
            if title and url:
                out.append({"title": title[:160], "authors": authors,
                            "url": url, "summary": summary})
    except ET.ParseError:
        return []
    return out


# --- Open Library: books -----------------------------------------------------

def openlibrary_books(topic: str, n: int = 3) -> list[dict]:
    """[{title, authors, url}] from the Open Library search API."""
    r = _get("https://openlibrary.org/search.json",
             params={"q": topic, "limit": n, "fields": "title,author_name,key"})
    if r is None:
        return []
    out = []
    try:
        for doc in r.json().get("docs", [])[:n]:
            title = (doc.get("title") or "").strip()
            if not title:
                continue
            out.append({
                "title": title[:160],
                "authors": ", ".join((doc.get("author_name") or [])[:2]),
                "url": "https://openlibrary.org" + (doc.get("key") or ""),
            })
    except Exception:  # noqa: BLE001
        return []
    return out


# --- page content ------------------------------------------------------------

_JUNK = re.compile(r"(sign in|log in|enable javascript|cookies?|404|access denied|"
                   r"page not found|subscribe to|create an account)", re.IGNORECASE)


def fetch_page_text(url: str, cap: int = 1500) -> str:
    """The readable text of a web page (tags stripped) — for syllabus topic
    lists and module source material. Filters junk pages. Best-effort, capped."""
    r = _get(url)
    if r is None:
        return ""
    text = r.text
    text = re.sub(r"(?is)<(script|style|noscript|svg|head|nav|footer|header|form)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    # Reject login walls / error pages / near-empty shells.
    if len(text) < 300 or (len(text) < 800 and _JUNK.search(text[:400])):
        return ""
    return text[:cap]


# --- digests for agent prompts ----------------------------------------------

# Where real curricula live. Scoped search first; generic search fills gaps.
_UNI_SITES = ("site:stanford.edu OR site:ocw.mit.edu OR site:mit.edu OR "
              "site:berkeley.edu OR site:cmu.edu OR site:harvard.edu")


def curriculum_digest(goal: str) -> tuple[str, list[dict]]:
    """Research how universities actually teach this — returns (digest, sources).

    Searches top-university domains for syllabi, FETCHES the actual pages so
    the Principal sees real topic lists (not just titles), and adds a topic
    overview. The digest goes into the Principal's prompt; sources land in
    the library.
    """
    sources: list[dict] = []
    lines: list[str] = []

    wiki = wikipedia_summary(goal)
    if wiki:
        sources.append({"kind": "article", "title": wiki["title"],
                        "authors": "Wikipedia", "url": wiki["url"],
                        "summary": wiki["summary"]})
        if wiki["summary"]:
            lines.append(f"Overview ({wiki['title']}): {wiki['summary']}")

    uni_hits = search_web(f"{goal} course syllabus ({_UNI_SITES})", n=4)
    oer_hits = search_web(f"{goal} (site:openstax.org OR site:saylor.org OR "
                          f"site:khanacademy.org OR site:ocw.mit.edu)", n=3)
    gen_hits = search_web(f"{goal} university course syllabus curriculum topics", n=4)
    uni_hits = uni_hits + oer_hits
    seen: set[str] = set()
    hits = [h for h in uni_hits + gen_hits
            if not (h["url"] in seen or seen.add(h["url"]))]

    for h in hits[:6]:
        sources.append({"kind": "curriculum", "title": h["title"],
                        "authors": "web", "url": h["url"], "summary": ""})
    if hits:
        lines.append("University course pages found: "
                     + "; ".join(h["title"] for h in hits[:6]))

    # Read the top syllabus pages — the actual topics real programs teach.
    excerpts = []
    for h in hits[:3]:
        text = fetch_page_text(h["url"], cap=900)
        if text:
            excerpts.append(f"--- {h['title']} ({h['url']}):\n{text}")
    if excerpts:
        lines.append("Syllabus excerpts (actual topic coverage):\n" + "\n".join(excerpts))

    return ("\n".join(lines), sources)
