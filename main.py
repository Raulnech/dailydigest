"""AI Morning Brief: fetch news -> Claude explains it -> build web page -> notify.

Usage:
    python main.py                 # full run: fetch, summarise, build site, notify
    python main.py --no-notify     # build the site but don't send a notification
    python main.py --notify-only   # just send the notification for the latest digest
    python main.py --sample        # build the site from sample data (no API key needed)
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from brief import config
from brief.notify import send_notification

DATA = Path(config.OUTPUT_DIR) / "data"
HISTORY_DAYS = 7


def load_history() -> list[dict]:
    path = DATA / "history.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def notify_latest() -> None:
    latest = json.loads((DATA / "latest.json").read_text(encoding="utf-8"))
    site_url = os.environ.get("SITE_URL", "")
    first = latest["talking_points"][0] if latest["talking_points"] else "Your digest is ready."
    send_notification(
        title=f"AI Morning Brief · {latest['date_label']}",
        message=first,
        click_url=site_url,
    )


def build(sample: bool) -> None:
    from brief.render import render_site

    now = datetime.now(ZoneInfo(config.TIMEZONE))
    date_iso = now.strftime("%Y-%m-%d")
    date_label = now.strftime("%A %d %B %Y").replace(" 0", " ")

    if sample:
        payload = json.loads(Path("sample_digest.json").read_text(encoding="utf-8"))
        digest, sources = payload["digest"], {int(k): v for k, v in payload["sources"].items()}
    else:
        from brief.articles import full_text_for
        from brief.fetch import fetch_candidates
        from brief.summarise import pick_stories, write_digest

        history = load_history()
        seen_links = {link for day in history for link in day.get("links", [])}

        print("Fetching feeds...")
        candidates = fetch_candidates(seen_links)
        print(f"  {len(candidates)} candidate stories")
        if len(candidates) < 5:
            raise SystemExit("Too few news items found. Are the feeds reachable?")

        print(f"Asking {config.MODEL} to pick today's stories...")
        picks = pick_stories(candidates, [h for day in history for h in day["headlines"]])
        by_id = {c.id: c for c in candidates}
        picked = [by_id[i] for p in picks for i in p.candidate_ids if i in by_id]

        print("Reading the full articles...")
        full_text = full_text_for(picked)
        readable = sum(any(i in full_text for i in p.candidate_ids) for p in picks)
        print(f"  full text for {readable} of {len(picks)} stories")

        print(f"Asking {config.MODEL} to write the digest...")
        result = write_digest(
            picks, candidates, full_text, date_label,
            recent_concepts=[c for day in history for c in day["concepts"]],
        )
        digest = result.model_dump()

        # Sources for each story, publisher links first
        sources = {}
        for n, pick in enumerate(picks):
            items = sorted((by_id[i] for i in pick.candidate_ids if i in by_id),
                           key=lambda c: "news.google.com" in c.link)
            sources[n] = [{"name": c.source, "link": c.link} for c in items[:3]]

        # Remember what we covered so tomorrow doesn't repeat it.
        stories = [s for sec in ("industry", "finance", "startups") for s in digest[sec]]
        history = [d for d in history if d["date"] != date_iso][-(HISTORY_DAYS - 1):]
        history.append({
            "date": date_iso,
            "headlines": [s["headline"] for s in stories],
            "concepts": [c["term"] for s in stories for c in s["concepts"]],
            "links": [c.link for c in picked],
        })
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    print("Building site...")
    page = render_site(digest, sources, date_iso, date_label)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "latest.json").write_text(
        json.dumps({"date_label": date_label, "talking_points": digest["talking_points"]}, indent=2),
        encoding="utf-8",
    )
    print(f"  wrote {page}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-notify", action="store_true")
    parser.add_argument("--notify-only", action="store_true")
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()

    if not args.notify_only:
        build(sample=args.sample)
    if not args.no_notify and not args.sample:
        notify_latest()
