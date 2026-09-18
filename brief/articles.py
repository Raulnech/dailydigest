"""Step 2b: download the full text of the chosen stories.

Many sites allow this (TechCrunch, CNBC, The Verge, Crunchbase). Some don't
(paywalls, Google News redirect links, Finextra). When it fails we fall back
to the headline and RSS snippet.
"""

from concurrent.futures import ThreadPoolExecutor

import trafilatura

from . import config
from .fetch import Candidate


def _download(link: str) -> str:
    if "news.google.com" in link:
        return ""  # Google News links redirect with JavaScript; can't follow them
    try:
        page = trafilatura.fetch_url(link)
        return (trafilatura.extract(page) or "") if page else ""
    except Exception:
        return ""


def full_text_for(candidates: list[Candidate]) -> dict[int, str]:
    """Returns {candidate id: article text} for every article we could read."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        texts = pool.map(_download, [c.link for c in candidates])
    return {
        c.id: text[: config.MAX_ARTICLE_CHARS]
        for c, text in zip(candidates, texts)
        if len(text) > 500
    }
