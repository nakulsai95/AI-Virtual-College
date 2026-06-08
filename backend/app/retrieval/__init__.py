"""Grounding: gather real learning materials to inform the curriculum.

Sources (all degrade gracefully when offline / unconfigured):
  - open_index : a curated catalogue of OPEN, linkable resources (MIT OCW,
                 OpenStax, official docs, freeCodeCamp). No network, always on,
                 legally clean — we link, never copy.
  - arxiv      : open-access papers via the arXiv API (keyless).
  - search     : general web/university/syllabus search via a user-supplied
                 Search API key (Tavily). Optional.

We retrieve and CITE; we never scrape copyrighted books or paywalled papers.
"""
from .aggregate import gather

__all__ = ["gather"]
