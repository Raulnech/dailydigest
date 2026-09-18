"""Step 2: Claude picks the important stories, then writes them up as lessons.

Two calls:
  1. pick_stories  - reads ~400 headlines, chooses the most important few
  2. write_digest  - reads the full articles and writes the digest
"""

from typing import Literal

import anthropic
from pydantic import BaseModel

from . import config
from .fetch import Candidate

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


# ---------- Call 1: choose stories ----------

class Pick(BaseModel):
    section: Literal["industry", "finance", "startups"]
    candidate_ids: list[int]  # all candidates covering this same story


class Selection(BaseModel):
    picks: list[Pick]


PICK_PROMPT = f"""You are the editor of a daily news digest for {config.READER}.

From the candidate news items, choose the stories with the biggest consequences for the AI and fintech industries, and the most to teach this reader. Favour: frontier labs and big tech strategy, how LLMs are built and used, chips and data centres, enterprise adoption, regulation, AI in banking/payments/insurance/asset management, how AI is financed (debt, capex, IPOs, market moves), notable funding rounds and acquisitions.

Skip product reviews, how-to guides, event promotions, opinion pieces with no news, and minor app updates. Skip stories already covered recently unless there is a meaningful new development.

For each story, list every candidate id that covers the same event (so we can find a readable full article). You may move a story to a better section than the one it was found in."""


def pick_stories(candidates: list[Candidate], recent_headlines: list[str]) -> list[Pick]:
    counts = ", ".join(f"{n} {s}" for s, n in config.STORIES_PER_SECTION.items())
    listing = "\n".join(f"[{c.id}] ({c.section}) {c.title} | {c.source}" for c in candidates)
    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=8000,
        system=PICK_PROMPT,
        messages=[{"role": "user", "content": (
            f"Choose exactly {counts} stories.\n\n"
            "Recently covered (avoid repeats):\n"
            + ("\n".join(f"- {h}" for h in recent_headlines) or "- none")
            + f"\n\nCandidates:\n{listing}"
        )}],
        output_config={"effort": "low"},
        output_format=Selection,
    )
    _check(response)
    return response.parsed_output.picks


# ---------- Call 2: write the digest ----------

class Concept(BaseModel):
    term: str
    explanation: str


class Story(BaseModel):
    story_number: int
    headline: str
    standfirst: str
    paragraphs: list[str]
    concepts: list[Concept]
    why_it_matters: str


class CodeCorner(BaseModel):
    title: str
    linked_story_number: int
    intro: str
    code: str
    walkthrough: list[str]
    try_it: str


class QuizQuestion(BaseModel):
    scenario: str
    question: str
    options: list[str]
    correct_option: int
    explanation: str
    concepts_tested: list[str]


class Digest(BaseModel):
    talking_points: list[str]
    industry: list[Story]
    finance: list[Story]
    startups: list[Story]
    code_corner: CodeCorner
    quiz: list[QuizQuestion]


WRITE_PROMPT = f"""You write a daily morning digest for {config.READER}. It is part newspaper, part lesson: after reading it they should understand what happened in AI and fintech, and have learned the concepts behind it.

## Articles
Write each story as a short news article, 200-300 words in 3-4 paragraphs:
- headline: specific, with the key number or name.
- standfirst: one sentence summing up the story, in the style of a newspaper subheading.
- paragraphs: open with what happened, then the context and background, then what happens next or what's at stake. Write clear, lively prose for an intelligent reader who is new to the field. When you first use a key term, keep the sentence understandable without the definition.
- Only state facts found in the source material. If a story only has a headline and snippet, keep that article shorter (100-150 words) rather than filling it with guesses. Say "reportedly" for claims from a single outlet or unconfirmed reports. Never invent figures, quotes, names or dates.
- Write in your own words. Do not copy sentences from the sources.

## Key concepts
For each article, list every term a beginner would need explained to fully understand it, usually 2-4. Each explanation is 1-3 sentences in plain English, ideally with an everyday analogy or a quick example with numbers. Don't reuse concepts listed as recently used unless the article depends on them (then give a one-line reminder). Across the whole digest, include at least one concept about how LLMs work (e.g. tokens, context window, fine-tuning, inference, RAG, agents, evals) whenever the news allows.

## Why it matters for you
2-3 sentences: which jobs or skills this creates demand for, how to bring it up in an interview, or how it links to another story today.

## Code corner
One short, runnable Python example (standard library only, under 25 lines) connected to one of today's stories. Rotate between: Python fundamentals applied to finance data (e.g. calculating valuations, interest, returns), working with data (lists, dictionaries, CSV, JSON), and how software talks to LLMs (API requests, prompts, tokens, JSON outputs; use a fake response rather than a real API call so it runs without a key). Beginner level: explain each important line in walkthrough, then give a small try_it exercise that changes the code.

## Quiz
3-4 scenario questions. Each puts the reader in a realistic situation (an interview, a first week as an analyst at a bank, a startup pitch meeting, a team meeting deciding whether to use an LLM) and tests whether they can apply the concepts from today's articles, not whether they remember facts. Between them, the questions must cover concepts from all three sections. 4 options each, one clearly correct, with plausible wrong answers. correct_option is the 0-based index. The explanation says why the right answer is right and why the most tempting wrong answer is wrong.

## Talking points
Exactly 3 short sentences: "things to be able to say today".

Use British English."""


def write_digest(picks: list[Pick], candidates: list[Candidate], full_text: dict[int, str],
                 date_label: str, recent_concepts: list[str]) -> Digest:
    by_id = {c.id: c for c in candidates}
    blocks = []
    for n, pick in enumerate(picks):
        items = [by_id[i] for i in pick.candidate_ids if i in by_id]
        block = [f"### Story {n} (section: {pick.section})"]
        for c in items:
            block.append(f"- {c.title} | {c.source}" + (f"\n  {c.snippet}" if c.snippet else ""))
        article = next((full_text[c.id] for c in items if c.id in full_text), None)
        block.append(f"\nFull article:\n{article}" if article else "\n(No full article available: headline and snippet only.)")
        blocks.append("\n".join(block))

    user_message = (
        f"Today is {date_label}.\n\n"
        f"Recently used concepts: {', '.join(recent_concepts) or 'none'}\n\n"
        "Write the digest from these stories. Put each story in the section shown, "
        "and set story_number to match.\n\n" + "\n\n".join(blocks)
    )

    with client.messages.stream(
        model=config.MODEL,
        max_tokens=64000,
        system=WRITE_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_config={"effort": "medium"},
        output_format=Digest,
    ) as stream:
        response = stream.get_final_message()
    _check(response)
    print(f"  tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out")
    return response.parsed_output


def _check(response) -> None:
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined the request. Try running it again.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude's reply was cut off. Increase max_tokens in summarise.py.")
