"""Step 2: ask Claude to pick the important stories and explain them simply."""

from typing import Literal

import anthropic
from pydantic import BaseModel

from . import config
from .fetch import Candidate


class Story(BaseModel):
    headline: str
    what_happened: str
    plain_english: str
    concept_term: str
    concept_definition: str
    why_it_matters: str
    source_ids: list[int]


class Term(BaseModel):
    term: str
    definition: str


class QuizItem(BaseModel):
    question: str
    answer: str


class Digest(BaseModel):
    talking_points: list[str]
    industry: list[Story]
    finance: list[Story]
    startups: list[Story]
    vocabulary: list[Term]
    quiz: list[QuizItem]


SYSTEM_PROMPT = """You write a daily morning news digest for one reader: someone trying to land an entry-level job in AI. They are learning Python and are new to the business and finance side of the industry. The digest exists to build their commercial awareness, so every story should teach them something they can use in an interview or networking conversation.

Choosing stories:
- Pick the stories with the biggest consequences for the AI industry, not the most clickable. Favour: frontier labs and big tech strategy, chips and data centres, enterprise adoption, regulation, AI in banking/insurance/asset management, how AI is being financed (debt, capex, IPOs, market moves), notable funding rounds and acquisitions.
- Skip product reviews, how-to guides, opinion pieces with no news, and minor app updates.
- When several items cover the same event, treat them as one story and cite all of them.
- Skip anything already covered recently (listed by the user) unless there is a meaningful new development.

Writing each story:
- headline: specific, includes the key number or name.
- what_happened: 2-3 sentences of facts. Only state facts present in the candidate headlines and snippets. If something is reported by a single outlet or is unconfirmed, say "reportedly". Never invent figures, quotes or dates.
- plain_english: explain it like you would to a smart friend who doesn't work in tech or finance. Use an everyday analogy where it genuinely helps. Don't be patronising.
- concept_term / concept_definition: ONE term the story teaches (e.g. "Series B", "inference", "capex", "explainability") and a one-sentence definition. Don't reuse concepts listed as recently used.
- why_it_matters: the career angle. Which jobs or skills this creates demand for, how to bring it up in an interview, or how it connects to another story today.
- source_ids: the candidate ids the story is based on.

Also write:
- talking_points: exactly 3 short sentences, "things to be able to say today", each drawing on today's stories.
- vocabulary: 4 useful terms from today's news with plain definitions.
- quiz: 3 questions that check understanding of today's concepts (not trivia about dates), each with a short explanatory answer.

Use British English. Be concise: the whole digest should take 6-8 minutes to read."""


def _format_candidates(candidates: list[Candidate]) -> str:
    lines = []
    for c in candidates:
        line = f"[{c.id}] ({c.section}) {c.title} | {c.source}"
        if c.snippet and c.snippet.lower() not in c.title.lower():
            line += f"\n     {c.snippet}"
        lines.append(line)
    return "\n".join(lines)


def write_digest(candidates: list[Candidate], date_label: str,
                 recent_headlines: list[str], recent_concepts: list[str]) -> Digest:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    counts = ", ".join(f"{n} {s}" for s, n in config.STORIES_PER_SECTION.items())
    user_message = (
        f"Today is {date_label}. Write today's digest with {counts} stories.\n\n"
        f"Recently covered headlines (avoid repeats):\n"
        + ("\n".join(f"- {h}" for h in recent_headlines) or "- none")
        + "\n\nRecently used concepts (pick different ones):\n"
        + (", ".join(recent_concepts) or "none")
        + f"\n\nCandidate news items from the last {config.LOOKBACK_HOURS} hours:\n\n"
        + _format_candidates(candidates)
    )

    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_config={"effort": "medium"},
        output_format=Digest,
        timeout=600,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to write today's digest. Try running it again.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The digest was cut off. Increase max_tokens in summarise.py.")

    usage = response.usage
    print(f"  tokens: {usage.input_tokens} in / {usage.output_tokens} out")
    return response.parsed_output
