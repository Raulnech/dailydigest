# AI Morning Brief: vision and roadmap

*Research report, 18 September 2026. Written for the project owner. Jargon is explained the first time it appears.*

---

## 1. Summary

**Where you are.** You already have a working daily pipeline: the code collects headlines, has Claude pick and explain the important ones, turns them into a web page, and sends a push notification to your phone. It runs every morning on GitHub for free. Being able to show that on your CV is useful in itself, because it is a real, automated LLM application.

**Where you want to go.** You want a daily **news and learning** tool for people trying to break into AI and fintech. It would build commercial awareness, teach Python, and explain how LLMs work, using short readable articles, beginner explanations and quizzes set in realistic work situations.

**The main gap.** Today every edition stands alone. The news is random, the quiz only tests today, and nothing builds on what you learned last week. The research on learning is clear here. The two techniques with the strongest evidence are **retrieval practice** (testing yourself instead of re-reading) and **spaced practice** (coming back to material after gaps that get longer). Neither needs a login or a database to add. You can bring back older concepts in the quiz on a fixed schedule (1, 3, 7, 14 and 30 days after they first appeared) using a slightly larger version of the `history.json` file you already keep.

**Top recommendations**
1. **Now:** Keep a record of every concept the digest has taught, and make each day's quiz about half today's concepts and half older ones that are due for review. This is the biggest learning gain for the least code.
2. **Now:** Add a simple fact-check step, a curriculum "theme of the week", and a notification when the daily run fails.
3. **Now:** Stay on the right side of copyright. Explain in your own words, quote briefly and link to the source, and never commit extracted article text into `docs/`.
4. **Next:** A glossary page that grows over time, a weekly recap with interview-style questions, and progress tracking stored in the reader's browser.
5. **Later:** Email delivery, personalisation, and an "explain it again, simpler" option that is written in advance rather than generated live.

Running costs stay small: about £4–12 a month in API fees on Sonnet 5 (my estimate; see §5.6). GitHub Actions and Pages cost nothing for a public repo.

---

## 2. What's built today

The whole project is about 300 lines of Python. It works like an assembly line with four stations, all run by [`main.py`](../main.py):

| Step | File | What it does, in plain English |
|---|---|---|
| Settings | [`brief/config.py`](../brief/config.py) | One place for everything you might change: which Claude model to use (currently `claude-sonnet-5`), your timezone, how far back to look for news (28 hours), how many stories per section (4 industry, 3 finance, 3 startups), and the list of about 15 **RSS feeds**. An RSS feed is a machine-readable list of a website's latest articles. |
| 1. Fetch | [`brief/fetch.py`](../brief/fetch.py) | Reads each feed with the `feedparser` library and keeps items from the last 28 hours. It removes duplicate headlines (two outlets covering the same story) and any link used in the past week. Each item becomes a "candidate" with a title, source, link and a snippet of up to 400 characters. Google News search feeds fill the gaps for finance and funding stories. |
| 2. Summarise | [`brief/summarise.py`](../brief/summarise.py) | Sends every candidate to Claude together with a long **system prompt**: standing instructions that describe the reader and the rules, such as "only state facts present in the snippets" and "say 'reportedly' if unconfirmed". Claude's reply is forced into a fixed shape (**structured output**, checked by **Pydantic** models, which are Python classes that describe what valid data looks like): stories, talking points, vocabulary and a quiz. |
| 3. Render | [`brief/render.py`](../brief/render.py) + [`brief/templates/digest.html`](../brief/templates/digest.html) | **Jinja2** (a templating library: an HTML page with blanks that Python fills in) builds `docs/index.html` and a dated copy in `docs/archive/`. GitHub Pages publishes the `docs/` folder at <https://raulnech.github.io/dailydigest/>. The quiz uses `<details>` elements that you tap to reveal the answer. |
| 4. Notify | [`brief/notify.py`](../brief/notify.py) | Posts a message to your **ntfy** topic (ntfy is a free push-notification service). Your phone shows it, and tapping it opens the page. |
| Schedule | [`.github/workflows/daily.yml`](../.github/workflows/daily.yml) | **GitHub Actions** (GitHub's free computers that run scripts for you) runs the pipeline at 05:30 UTC every day, commits the new `docs/`, waits 90 seconds for Pages to update, then sends the notification. |
| Memory | `docs/data/history.json` | Seven days of headlines, concept terms and links, so tomorrow's digest doesn't repeat itself. **Note: this file sits in `docs/`, so it is public.** |

**Being changed right now (assumed to land):** stories become 200–300 word articles written from the full article text where it can be extracted. The **trafilatura** library does the extraction; it works for TechCrunch, CNBC, The Verge and Crunchbase, but not for Google News redirect links or Finextra, which fall back to the headline and snippet. Also coming: a full list of explained concepts for every article, a daily "Code corner" Python snippet, and a multiple-choice quiz built around scenarios.

---

## 3. The vision (in your terms)

A daily tool for people like you who want to get into AI or fintech. Every morning it should:

- **Build commercial awareness** across three areas: the AI industry, AI and finance, and startups and funding. The aim is that you can hold your own in an interview or a networking chat.
- **Teach you to code,** a little Python each day, tied to something real.
- **Teach you how LLMs work,** so the news about models, chips and agents makes sense.
- **Be readable:** short articles, with every concept explained for a beginner and nothing assumed.
- **Test you with realistic scenarios.** Instead of "what is capex?", a question like "your manager asks why Microsoft's share price fell after it raised capex guidance. What do you say?"

---

## 4. Gap analysis: today vs vision

| Vision | Today (including the in-flight changes) | Gap |
|---|---|---|
| Commercial awareness | Strong. Good feed mix, a clear "why it matters" career angle, talking points | Stories are chosen by importance alone, with no link to what you're learning this week. Finance coverage relies on Google News links whose full text can't be extracted |
| Learn to code | "Code corner" snippet (in progress) | There's no sequence: day 40 could be easier than day 3. You read code but never write it, and there's no exercise |
| Understand LLMs | Only when a story happens to touch it | There's no LLM track at all, and concepts appear at random |
| Every concept explained | Covered (in progress) | Explanations vanish after one day. There's no glossary to look things up in later |
| Scenario quizzes | Covered (in progress) | Quizzes test **today only**. Nothing comes back after 3, 7 or 30 days, which is where most of the learning benefit comes from (§5.2) |
| Habit | Push notification plus a home-screen shortcut | No streak, no sense of progress, no weekly recap |
| Trustworthy | Prompt rules against making things up | No automated check that numbers and names in the output appear in the source text. A failed run fails silently (you just don't get a notification) |
| For "people like me" | A single hard-coded reader (the owner) | No email sign-up and no way to share. Fine for now; see open questions |

---

## 5. Research findings

### 5.1 Comparable products: what works

| Product | Format | What to borrow |
|---|---|---|
| **TLDR AI** | Daily, about a 5-minute read. Each item is a few sentences plus a link. About 1.1M readers, reported 47% open rate ([Readless](https://www.readless.app/newsletters/tldr-ai), [tldr.tech](https://tldr.tech/ai)) | Ruthless brevity. Link out instead of retelling at length |
| **The Rundown AI** | Daily, "5 minutes", easy to skim, conversational, 2M+ subscribers ([therundown.ai](https://www.therundown.ai/), [DataCamp](https://www.datacamp.com/blog/best-ai-newsletters)) | Pair each news item with "how to apply it" |
| **Superhuman AI** | Strictly 3 minutes, Monday to Friday. Ends with 3–5 "things you can use today" ([superhuman.ai](https://www.superhuman.ai/), [Readless review](https://www.readless.app/blog/superhuman-ai-newsletter-review-2026)) | A fixed, predictable length and a practical takeaway |
| **The Batch (DeepLearning.AI)** | Weekly. Andrew Ng's personal letter, then stories that explain less familiar terms along the way ([The Batch](https://www.deeplearning.ai/the-batch/about)) | Explaining terms inline, and a weekly reflective piece. This is the closest model for your "learn while reading" goal |
| **Ben's Bites** | Daily, for builders. Includes mini-tutorials and tools being tested ([Growth in Reverse](https://growthinreverse.com/bens-bites/)) | The mini-tutorial is essentially your Code corner |
| **Finimize** | "3 minutes", no jargon, aimed at new investors. About 850k readers. Each story covers what happened, then why it matters ([Finimize](https://finimize.com/), [Wealth Pursuits review](https://wealthpursuits.com/finimize-review/)) | The best model for your finance section: plain language plus "why it matters" |
| **Morning Brew** | A 5-minute morning habit with a witty voice. Referral rewards drove about 30% of subscriber growth ([ReferralRock](https://referralrock.com/blog/morning-brew-referral-program/), [SparkLoop](https://sparkloop.app/blog/the-secrets-behind-morning-brews-growth-to-2-million-newsletter-subscribers-6)) | Consistent timing and voice. The ask to share comes only at the end |
| **Fintech Brainfood** | Weekly deep dive plus the "Weekly Rant" opinion piece. 47k+ readers ([fintechbrainfood.com](https://www.fintechbrainfood.com/)) | A weekly opinionated synthesis ("what this week meant") alongside the daily facts |
| **Duolingo** | Bite-sized lessons, streaks and streak freezes. Duolingo reports that users with 7-day streaks are about 3.6x more likely to finish a course, and that streak freezes cut churn among at-risk users by about 21% ([StriveCloud](https://www.strivecloud.io/duolingo-gamification-explained), [justanotherpm](https://www.justanotherpm.com/blog/the-psychology-behind-duolingos-streak-feature)) | Streaks work, and **forgiveness** (freezes) makes them work better. Caveat: these figures are company-reported and repeated by secondary blogs, and I couldn't find the original data |
| **Brilliant** | No videos. You learn by solving interactive problems with instant feedback ([Brilliant FAQ](https://brilliant.org/faq/)) | Put a question *before* the explanation sometimes ("what do you think happens if…?") |

**Patterns across them:** (1) a fixed, short length of 3–5 minutes, (2) a predictable structure every day, (3) "why it matters" after every fact, (4) a weekly longer piece for synthesis, and (5) a habit loop of the same time, a streak and a small reward. Your planned 10 stories × 200–300 words comes to 2,000–3,000 words, or **10–15 minutes**. That's two to three times longer than the market leaders. Consider 3 full articles plus 5–7 "quick hits" of two sentences each.

### 5.2 Learning science that should shape the design

The standard review is Dunlosky et al. (2013), which rated ten study techniques. Only two got the top "high utility" rating: **practice testing** and **distributed (spaced) practice** ([APS summary](https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html), [AFT version](https://www.aft.org/ae/fall2013/dunlosky)). Re-reading and highlighting, which is essentially what reading a digest is, rated *low*.

- **Retrieval practice (the "testing effect").** Pulling something out of memory strengthens it more than reading it again. In Roediger & Karpicke (2006), students who tested themselves remembered 61% of a passage a week later, against 40% for those who re-read it ([paper](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2006.01693.x)). *So the quiz is the most valuable part of the page, not an add-on.*
- **Multiple choice can work, if the distractors are good.** Little & Bjork found that multiple-choice questions with *plausible, competitive* wrong answers improve later recall, including of related material that wasn't tested ([paper](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2017/01/LittleBjorkMC2014.pdf)). *Tell Claude that each wrong option must be a common misconception, and that each option needs a one-line explanation of why it's right or wrong ("elaborated feedback").*
- **Spacing.** Reviews spread over growing intervals beat cramming. Modern schedulers such as **FSRS** (the open-source algorithm now used by Anki) adapt the interval to each person's answers and need 20–30% fewer reviews than the older SM-2 method ([FSRS wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/ABC-of-FSRS)). A Python library exists. But your site has no logins, so you can't record individual answers on the server. A **fixed schedule** is the right starting point.
- **Interleaving.** Mixing different kinds of problems beats practising one kind in a block. A randomised trial with 787 students found a large effect (d = 0.83) ([Rohrer et al. 2020](https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)). *Mix finance, AI and Python questions in one quiz rather than grouping them by section.*
- **Worked examples.** Beginners learn more from studying a fully worked solution than from solving problems unaided, and "fading" (removing steps one at a time) builds independence ([MIT TLL](https://tll.mit.edu/teaching-resources/how-people-learn/worked-examples/), [ACM TOCE 2025](https://dl.acm.org/doi/full/10.1145/3732791)). *Code corner: show the full snippet with comments on Monday, leave one line blank for you to fill on Wednesday, ask you to write it on Friday.*
- **Scenario-based learning.** Clark & Mayer argue that realistic workplace scenarios speed up expertise and help people apply what they learned at work, rather than just remembering it ([Wiley](https://www.wiley.com/en-us/Scenario+based+e+Learning:+Evidence+Based+Guidelines+for+Online+Workforce+Learning-p-9781118127254)). This supports your scenario idea. My honest caveat is that the evidence is less rigorous than for testing and spacing, so treat it as good practice rather than proven.

**How to bring back yesterday's and last week's concepts (concretely):**

1. Replace the 7-day `history.json` with a longer-lived `concepts.json`. It's one entry per concept: `term`, `definition`, `track` (industry / finance / startups / python / llm), `first_seen` date, and the story it came from. Keep 60 days or more; it's small.
2. Each day, work out which concepts are **due**, meaning first seen exactly 1, 3, 7, 14 or 30 days ago (Leitner-style expanding intervals).
3. Pass Claude the due concepts along with the news and ask for a 5-question quiz: **2 on today's concepts, 2 on due concepts, 1 mixed "connect two ideas" question.** The review questions should use *today's* news as the new scenario ("Yesterday you learned about Series B rounds. Today Arcee raised… Which stage is this?"). That gives spacing, interleaving and transfer in one question.
4. Label each question with where it came from ("from 7 days ago") so you can see the spacing working.
5. Later, save answers in the reader's browser (`localStorage`) and move concepts you get wrong to shorter intervals. That brings the design close to FSRS without a server.

### 5.3 Curriculum: 12 weeks, three tracks

The fix for "random news" is a **theme of the week** for each track. The daily prompt gets the week's themes and is told to: (a) prefer a story that illustrates the finance or industry theme when one is available, (b) write the Code corner on the Python theme, using that day's data where possible, and (c) include one "How LLMs work" box on the LLM theme, linked to a story when it can be. The news stays real; the curriculum decides which angle you explain it from.

| Wk | Commercial awareness | Python | LLM fundamentals |
|---|---|---|---|
| 1 | How tech companies make money: revenue, margins, subscriptions vs usage-based pricing | Variables, strings, `print`, f-strings | What an LLM is: next-token prediction |
| 2 | The AI value chain: chips → cloud → model labs → apps | Lists, dicts, loops | Tokens and context windows (why pricing is per token) |
| 3 | Startup funding: seed → Series A/B/C, dilution, valuation | Functions; reading this project's `fetch.py` | Training vs inference; why inference costs money |
| 4 | Public markets: shares, market cap, earnings, guidance | Files and JSON (read `history.json`) | Pre-training, fine-tuning, RLHF (learning from human feedback) |
| 5 | Capex, data centres and how AI is financed (debt, private credit) | APIs and `requests`; calling a free API | Prompting basics; system prompts (read `summarise.py`) |
| 6 | Banking 101: how banks earn money, where AI fits (fraud, KYC, credit) | `pandas` basics: DataFrames | Hallucination and grounding; why sources matter |
| 7 | Payments and fintech: cards, open banking, stablecoins | `pandas`: groupby, simple stats | Embeddings and retrieval (RAG), explained simply |
| 8 | Regulation: EU AI Act, FCA/SEC, model risk management | Plotting with `matplotlib` | Evaluation: how you tell if an LLM app is good |
| 9 | M&A and "acqui-hires"; big tech strategy | Classes and Pydantic (the digest's own models) | Structured outputs and tool use / agents |
| 10 | Asset management and trading: where AI actually gets used | Calling the Claude API yourself | Cost, latency and model choice (Opus vs Sonnet vs Haiku) |
| 11 | Unit economics: CAC, LTV, burn, runway | A tiny project: a stock or news tracker | Safety, bias and security (prompt injection) |
| 12 | Putting it together: pitch a company in 2 minutes | Git and GitHub Actions (how *this* project runs) | Build and explain your own mini LLM app |

Using your own project as teaching material (weeks 3, 4, 5, 9 and 12) is deliberate: it turns the tool into a portfolio piece you can explain in an interview. Free reference material to link from the page: Karpathy's one-hour [Intro to Large Language Models](https://www.youtube.com/watch?v=zjkBMFhNj_g), the free [Hugging Face LLM course](https://huggingface.co/learn/llm-course/en/chapter1/1), and Anthropic's [prompt engineering tutorial](https://github.com/anthropics/courses). After week 12, loop round with harder versions, or let the owner pick the next track.

### 5.4 Content sourcing and the copyright line

*I'm not a lawyer. This is general information, not legal advice.*

**Better sources of full text**

| Option | Full text? | Cost / terms | Verdict |
|---|---|---|---|
| RSS + trafilatura (current) | For some sites | Free. You fetch pages as a normal reader would | Fine for *reading* to write a summary. Respect `robots.txt` and don't hammer sites |
| Google News RSS links | No: they are redirect links | Google's terms restrict using the service to display its content elsewhere ([cloro summary](https://cloro.dev/blog/google-news-rss/)). Packages like `googlenewsdecoder` can recover the publisher URL ([PyPI](https://pypi.org/project/googlenewsdecoder)) | Decode the link to the publisher's URL, then extract from the publisher. Keep using Google News only for *discovery* |
| **The Guardian Open Platform** | Yes (the `body` field) | Free developer key. Sources disagree on whether a public site counts as commercial use ([PublicAPIs](https://publicapis.io/the-guardian-api), [APIScout](https://apiscout.dev/guides/best-news-apis-developers-2026)). **Check the terms yourself before relying on it** | A good legal full-text source for UK business and tech |
| NewsAPI.org free plan | No (snippets) | Development only, 24-hour delay, 100 requests a day ([NewsAPI pricing](https://newsapi.org/pricing)) | Not usable for a daily production run |
| Claude **web search / web fetch** tools | Fetch returns page text | Web search costs $10 per 1,000 searches plus tokens. Web fetch has no per-call fee, just tokens ([Anthropic](https://anthropic.com/news/web-search-api), [pricing overview](https://synthorai.io/blog/web-search-api-cost/)) | A useful fallback for the Finextra and Google News failures. Claude can open the link itself. About $0.01–0.10 a day extra |
| Company primary sources (press releases, investor relations, OpenAI/Anthropic blogs, SEC filings) | Yes | Free and meant to be shared | Under-used. They're primary sources, so they're more accurate *and* safer to use |

**The copyright line for a public GitHub Pages site**

- **Facts are free; wording is not.** Copyright protects *expression*, not the underlying facts. "Anthropic raised $X at a $Y valuation" is a fact anyone can report ([RCFP](https://www.rcfp.org/hot-news-case-could-impact-online-news-aggregation/), [Holland & Knight](https://www.hklaw.com/en/insights/publications/2011/06/hot-news-doctrine-substantially-preempted-by-us-co)).
- **UK law** has a fair-dealing exception for "reporting current events". It requires fairness (how much you take, and whether you damage the original's market) and acknowledgement of the source. It **does not cover photographs** ([Wikipedia overview](https://en.wikipedia.org/wiki/Fair_dealing_in_United_Kingdom_law), [Sprintlaw](https://sprintlaw.co.uk/articles/uk-copyright-fair-dealing-when-businesses-can-use-content-without-permission/)).
- **Where AI products have got into trouble:** outputs with "full or partial verbatim reproductions" of articles, and made-up text attributed to a publisher. That is the core of *Dow Jones v. Perplexity*, which survived Perplexity's motion to dismiss ([FindLaw](https://caselaw.findlaw.com/court/us-dis-crt-sd-new-yor/117622090.html), [CNBC](https://www.cnbc.com/2024/10/21/murdoch-firms-dow-jones-and-new-york-post-sue-perplexity-ai.html)). *Thomson Reuters v. Ross* (2025) also rejected fair use where copying produced a competing substitute ([DWT](https://www.dwt.com/blogs/artificial-intelligence-law-advisor/2025/02/reuters-ross-court-ruling-ai-copyright-fair-use)).

**Safe practice rules for this project:**
1. Use the full text **only as input** to Claude. **Never write extracted article text into `docs/`**, or anywhere else in the public repo. Check that the in-flight change doesn't cache it in `docs/data/`.
2. Tell Claude: write in your own words; quote at most one short phrase (under about 15 words) per article, in quotation marks and attributed; no paragraph-by-paragraph retelling.
3. Your articles should **add something**: the explanation, the concepts, the career angle. That's what makes them commentary and teaching rather than a substitute for the original. Keep them shorter than the source.
4. Always name the publisher and link to the original prominently.
5. Don't copy images. Don't reproduce paywalled articles in detail.
6. Keep the repo non-commercial. Adding ads or paid tiers changes the analysis.

### 5.5 Product features ranked by value vs effort

Effort: **S** is an evening, **M** is a weekend, **L** is several weekends. The ranking is for a beginner maintainer.

| # | Feature | Value | Effort | Key note |
|---|---|---|---|---|
| 1 | Spaced review in the quiz (§5.2) | Very high | S–M | The biggest learning gain for the least code |
| 2 | Curriculum theme of the week (§5.3) | High | S | A dict in `config.py` plus one paragraph of prompt |
| 3 | Growing glossary page | High | S | `concepts.json` rendered A–Z. Doubles as interview revision |
| 4 | Failure alert | High | S | `if: failure()` workflow step that sends an ntfy message |
| 5 | Fact check / grounding step | High | M | See §5.6 |
| 6 | Weekly recap + interview mode (Sunday) | High | M | 5 things that mattered, 5 "tell me about…" questions with model answers, a 10-question review |
| 7 | Progress and streak on the page | Medium | M | JavaScript + `localStorage` (per device, no login). Include a "freeze" day: forgiveness helps |
| 8 | "Explain it again, simpler" | Medium | S–M | **Pre-generate** it at build time. A live button would expose your API key |
| 9 | Shorter default read | Medium | S | 3 articles + quick hits, 5–7 minutes |
| 10 | Email delivery | Medium if shared | M | e.g. Buttondown or Resend free tiers (limits not verified) |
| 11 | Personalisation | Low for now | L | Needs accounts. Wait for real users |

### 5.6 Costs and risks of the current setup

| Area | Situation | Mitigation |
|---|---|---|
| **Claude API cost** | Sonnet 5 costs $2 per million input tokens and $10 per million output tokens. Opus 5 is $5/$25 (Anthropic pricing as of mid-2026). My estimate for the new longer format: about 30–60k input tokens (headlines plus full texts) and 15–25k output tokens (articles, quiz, code, plus Claude's thinking), so **roughly $0.20–0.40 a day, about £5–10 a month**. The README's "$0.25–0.50 with Opus" figure is out of date | The code already prints token counts, so log them to a CSV and check the real figure after a week. Set a monthly spend limit in the Claude Console. Trimming full texts to the first ~1,500 words keeps input cost down. The Batch API is 50% cheaper but results can take up to 24 hours, so it doesn't fit a morning deadline |
| **GitHub Actions** | Standard runners are free and unlimited for public repos ([GitHub Docs](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)). Scheduled runs can start 30+ minutes late. Scheduled workflows in public repos are **switched off after 60 days with no repository activity** ([GitHub Docs](https://docs.github.com/actions/managing-workflow-runs/disabling-and-enabling-a-workflow)) | The daily commit is probably enough to count as activity, but if the job fails for two months it will stop and stay stopped. The failure alert (#4) covers this. Making the repo private would cost minutes (2,000 free a month, which is still plenty) and Pages would need a paid plan |
| **ntfy topic privacy** | ntfy topics are "shared secrets": anyone who knows the name can read *and post* to it ([ntfy docs](https://docs.ntfy.sh/privacy/)) | The content is public news, so reading it is harmless. The risk is spam or fake messages with malicious links. Keep the long random topic name in GitHub Secrets (you already do). An access-token-protected reserved topic needs ntfy Pro. For now, only tap notifications that point to `raulnech.github.io` |
| **Feed breakage** | Feeds change their URL or format without warning. `fetch.py` prints a warning but carries on, and the run only stops if there are fewer than 5 candidates | Add a per-feed count to the log. Alert if a feed returns 0 items for 3 days in a row |
| **Hallucination** (the model stating things that aren't in its sources) | A large BBC/EBU study found AI assistants gave news answers with significant issues **45% of the time**, including 31% with sourcing problems ([EBU](https://www.ebu.ch/news/2025/10/ai-s-systemic-distortion-of-news-is-consistent-across-languages-and-territories-international-study-by-public-service-broadcaste)). That study covered chat assistants, not a tightly grounded pipeline like yours, but the risk is real, and longer articles give more room for errors | (1) Ask Claude to return, for every number and named entity in an article, the source ID it came from. (2) Have a cheap Python check confirm that each number actually appears in that source text, and flag or drop any that don't. (3) Optionally, a second low-cost Claude call to check "is every claim supported?". Anthropic's Citations feature does this natively but can't currently be combined with structured outputs, so the DIY check is simpler |
| **Public history file** | `docs/data/history.json` is published | Harmless today. Just don't put anything private or copyrighted there |
| **Secrets** | The API key is in GitHub Secrets, which is correct | Never add browser-side API calls, which would expose the key. Pre-generate everything |
| **Code upkeep** | `summarise.py` uses `output_format=` in `messages.parse`. Anthropic's current docs describe `output_config.format` as the replacement for the older parameter | Not urgent (the code works today), but worth checking against the SDK changelog when you next upgrade `anthropic` |

---

## 6. Recommended roadmap

### Now (next 1–2 weeks)

| Item | Why | Effort | Files |
|---|---|---|---|
| **Concept store + spaced-review quiz.** Keep all concepts 60+ days; the quiz is 2 today + 2 due (1/3/7/14/30 days) + 1 mixed; elaborated feedback on every option | Retrieval and spacing are the best-evidenced learning techniques. This single change turns a newsletter into a learning tool | M | `main.py` (history → `concepts.json`, raise `HISTORY_DAYS`), `brief/summarise.py` (quiz model and prompt), `brief/templates/digest.html` |
| **Theme of the week** for the three tracks | Ties random news to a sequenced curriculum | S | `brief/config.py` (a `CURRICULUM` dict keyed by week number), `brief/summarise.py` (prompt) |
| **Failure alert** | Right now a broken run is silent, and 60 days of failures means the schedule gets switched off | S | `.github/workflows/daily.yml` (an `if: failure()` step), `brief/notify.py` |
| **Copyright guardrails** | Keeps the public site on the safe side as articles get longer | S | `brief/summarise.py` (prompt rules), check that the in-flight extraction code keeps full text out of `docs/` |
| **Log token usage** | Replaces my cost estimate with real numbers | S | `brief/summarise.py`, `main.py` |

### Next (weeks 3–8)

| Item | Why | Effort | Files |
|---|---|---|---|
| Number/entity grounding check | Catches the most damaging kind of error: wrong figures you might repeat in an interview | M | `brief/summarise.py` (add `claims` to the Story model), new `brief/verify.py` |
| Glossary page | Makes concepts permanent and searchable. Good for interview revision | S | `brief/render.py`, new `brief/templates/glossary.html` |
| Sunday weekly recap + interview questions | Weekly synthesis and practice explaining things out loud | M | `main.py` (`--weekly` flag), `brief/summarise.py` (Weekly model), new template, `.github/workflows/daily.yml` (Sunday cron) |
| Decode Google News links + Claude web fetch fallback | Gets full text for the finance section, where extraction fails most | M | `brief/fetch.py`, `requirements.txt` |
| Shorter default: 3 articles + quick hits | Matches the 3–5 minute norm of the market leaders, so you're more likely to read it daily | S | `brief/config.py`, `brief/summarise.py`, template |
| Code corner with fading (full → fill-the-gap → write it) | Worked-example research for novices | S | `brief/summarise.py` (prompt), template |

### Later (month 3+)

| Item | Why | Effort | Files |
|---|---|---|---|
| Progress, streak and adaptive review in the browser | Habit loop. Moving missed concepts to shorter intervals approximates FSRS | M–L | template (JavaScript + `localStorage`) |
| Pre-generated "explain simpler" toggle | Beginner accessibility without exposing the API key | S–M | `brief/summarise.py`, template |
| Email delivery | Only if other people will read it | M | new `brief/email.py`, workflow secrets |
| Add primary sources (company IR/blog feeds, Guardian API if the terms allow) | More accurate and more clearly legal | M | `brief/config.py`, `brief/fetch.py` |
| Personalisation / multiple readers | Once there's an audience | L | Architecture change |

---

## 7. Open questions for the owner

1. **Who is it for?** Just you for now, or a public product for others? That decides whether email, sharing and a "what is this" landing page matter.
2. **How long do you actually want to read each morning?** 5 minutes (market norm) or 10–15 (the current plan)? Should weekends be different, for example a recap only?
3. **Which roles are you targeting?** AI product, data or analytics, fintech operations, sales engineering? The curriculum and interview questions should lean towards them.
4. **UK or US focus** for finance and regulation (FCA vs SEC, London vs New York)?
5. **Budget ceiling** for API spend per month? That decides Sonnet vs Opus and whether to add web fetch.
6. **Do you want to write code** (exercises you run yourself, perhaps in a linked Colab notebook) or mainly read it?
7. **Is keeping the repo public OK?** It's needed for free Pages, and it makes a good portfolio, but everything in `docs/` is visible.
8. **Should the curriculum repeat after 12 weeks** at a harder level, or move on to new tracks (for example SQL, statistics, product management)?
