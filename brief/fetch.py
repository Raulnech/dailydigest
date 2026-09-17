"""Step 1: collect recent headlines from RSS feeds."""

import calendar
import html
import re
import time
from dataclasses import dataclass

import feedparser

from . import config


@dataclass
class Candidate:
    id: int
    section: str
    title: str
    source: str
    link: str
    snippet: str
    published: float  # unix timestamp


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _normalise(title: str) -> str:
    """Used to spot the same story from two feeds."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower())[:70]


def fetch_candidates(seen_links: set[str] | None = None) -> list[Candidate]:
    seen_links = seen_links or set()
    cutoff = time.time() - config.LOOKBACK_HOURS * 3600
    seen_titles: set[str] = set()
    candidates: list[Candidate] = []

    for section, urls in config.FEEDS.items():
        for url in urls:
            feed = feedparser.parse(url, agent="Mozilla/5.0 (AI Morning Brief)")
            if feed.get("bozo") and not feed.entries:
                print(f"  ! could not read {url}")
                continue
            # "AI News & Artificial Intelligence | TechCrunch" -> "TechCrunch"
            feed_name = _clean(feed.feed.get("title", url)).split(" | ")[-1]

            for entry in feed.entries:
                stamp = entry.get("published_parsed") or entry.get("updated_parsed")
                if not stamp:
                    continue
                published = calendar.timegm(stamp)
                if published < cutoff:
                    continue

                title = _clean(entry.get("title", ""))
                source = feed_name
                # Google News titles look like "Headline - Publisher"
                if "news.google.com" in url and " - " in title:
                    title, source = title.rsplit(" - ", 1)

                key = _normalise(title)
                link = entry.get("link", "")
                if not title or key in seen_titles or link in seen_links:
                    continue
                seen_titles.add(key)

                candidates.append(Candidate(
                    id=len(candidates),
                    section=section,
                    title=title,
                    source=source,
                    link=link,
                    snippet=_clean(entry.get("summary", ""))[:400],
                    published=published,
                ))
    return candidates
