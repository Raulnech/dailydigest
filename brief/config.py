"""Everything you might want to tweak lives here."""

# Which Claude model writes the digest. "claude-opus-5" gives the best
# explanations; "claude-sonnet-5" costs roughly 60% less.
MODEL = "claude-sonnet-5"

# Who the digest is written for. Claude tailors explanations to this.
READER = (
    "someone breaking into AI and fintech: early in their career, learning Python, "
    "and wanting to understand how LLMs work and how the AI industry makes money"
)

# Your timezone, used for the date shown on the digest.
TIMEZONE = "Europe/London"

# How far back to look for news, in hours.
LOOKBACK_HOURS = 28

# How many stories per section. Each is a ~250-word article, so 8 stories
# is roughly a 15-minute read including concepts and the quiz.
STORIES_PER_SECTION = {"industry": 3, "finance": 3, "startups": 2}

# How much of each full article to send to Claude (characters).
MAX_ARTICLE_CHARS = 6000

# Google News search feeds are great for filling gaps in specific topics.
def _google_news(query: str) -> str:
    from urllib.parse import quote_plus
    return f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-GB&gl=GB&ceid=GB:en"

# RSS feeds, grouped by the section they most likely belong to.
# Claude can still move a story to a better section.
FEEDS = {
    "industry": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "https://arstechnica.com/ai/feed/",
        "https://openai.com/news/rss.xml",
        "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        _google_news('(OpenAI OR Anthropic OR "Google DeepMind" OR Nvidia OR Microsoft AI OR Meta AI)'),
    ],
    "finance": [
        "https://www.finextra.com/rss/headlines.aspx",
        _google_news('"artificial intelligence" (bank OR banking OR "hedge fund" OR "asset manager" OR insurer)'),
        _google_news('AI (stocks OR bubble OR capex OR "data center" debt OR IPO)'),
        _google_news('AI (FCA OR SEC OR "EU AI Act") finance'),
    ],
    "startups": [
        "https://techcrunch.com/category/venture/feed/",
        "https://news.crunchbase.com/feed/",
        _google_news('AI startup (raises OR "Series A" OR "Series B" OR seed OR valuation)'),
        _google_news('AI (acquires OR acquisition) startup'),
    ],
}

# Where the website is generated (GitHub Pages serves this folder).
OUTPUT_DIR = "docs"
