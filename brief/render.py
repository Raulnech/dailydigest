"""Step 3: turn the digest into web pages (today's page + an archive)."""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config

TEMPLATES = Path(__file__).parent / "templates"
SECTIONS = [
    ("industry", "The AI industry", "Big labs, big tech and the direction of travel."),
    ("finance", "AI & finance", "Where Wall Street and the City meet AI, as users and as funders."),
    ("startups", "Startups & funding", "Who raised, how much, and what investors are betting on."),
]


def _word_count(value) -> int:
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, dict):
        return sum(_word_count(v) for v in value.values())
    if isinstance(value, list):
        return sum(_word_count(v) for v in value)
    return 0


def render_site(digest: dict, sources: dict[int, list], date_iso: str, date_label: str) -> Path:
    out = Path(config.OUTPUT_DIR)
    (out / "archive").mkdir(parents=True, exist_ok=True)

    archive = sorted((p.stem for p in (out / "archive").glob("*.html")), reverse=True)
    if date_iso not in archive:
        archive.insert(0, date_iso)

    stories = {s["story_number"]: s for key, _, _ in SECTIONS for s in digest[key]}
    glossary = sorted(
        {c["term"].lower(): {**c, "story": s["story_number"]}
         for s in stories.values() for c in s["concepts"]}.values(),
        key=lambda c: c["term"].lower(),
    )

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape())
    template = env.get_template("digest.html")

    def page(root: str) -> str:
        return template.render(
            d=digest, sources=sources, sections=SECTIONS, stories=stories, glossary=glossary,
            date_label=date_label, date_iso=date_iso, minutes=max(5, round(_word_count(digest) / 230)),
            archive=archive[:30], root=root,
        )

    # Today's page lives at the site root so the link never changes...
    (out / "index.html").write_text(page(root="./"), encoding="utf-8")
    # ...and a permanent copy goes in the archive.
    (out / "archive" / f"{date_iso}.html").write_text(page(root="../"), encoding="utf-8")

    for static in ("manifest.webmanifest", "icon.svg"):
        (out / static).write_text((TEMPLATES / static).read_text(encoding="utf-8"), encoding="utf-8")
    (out / ".nojekyll").touch()
    return out / "index.html"
