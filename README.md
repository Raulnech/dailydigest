# AI Morning Brief

A daily digest of AI industry, AI & finance, and startup news, with every story explained in plain English. It runs by itself every morning in the cloud, publishes a web page, and sends a push notification to your phone and PC. Tap the notification and read.

```
RSS feeds ──► Claude picks & explains ──► web page (GitHub Pages) ──► ntfy push notification
             (brief/fetch.py)   (brief/summarise.py)   (brief/render.py)          (brief/notify.py)
```

Your PC doesn't need to be on. GitHub runs it for free.

## Cost

- GitHub, GitHub Pages and ntfy: free.
- Claude API: roughly $0.20–0.40 a day with Sonnet 5 (about £5–10 a month), set by `MODEL` in `brief/config.py`. Opus 5 writes better explanations but costs about 2.5× more. You can set a monthly spend limit in the Claude Console.

## One-time setup (about 15 minutes)

### 1. Get a Claude API key
Sign up at <https://console.anthropic.com>, add some credit, and create an API key. Keep it secret.

### 2. Put this folder on GitHub
Create a new **public** repository called `dailydigest` on <https://github.com/new> (GitHub Pages is free for public repos; the page only contains public news). Then in this folder:

```bash
git init
git add .
git commit -m "AI Morning Brief"
git branch -M main
git remote add origin https://github.com/Raulnech/dailydigest.git
git push -u origin main
```

### 3. Turn on GitHub Pages
Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`, folder: `/docs` → Save.
Your digest will live at `https://raulnech.github.io/dailydigest/`.

### 4. Pick a notification topic and install ntfy
Make up a hard-to-guess topic name, e.g. `ai-brief-7f3k9q2m` (anyone who knows it can see your notifications).

- **Phone:** install **ntfy** (App Store / Google Play) → + → subscribe to your topic.
- **PC:** open <https://ntfy.sh/app>, subscribe to your topic, and allow browser notifications. Tip: in Edge or Chrome, use *Install this site as an app* so notifications work like a desktop app.

### 5. Add secrets to GitHub
Repo → **Settings → Secrets and variables → Actions**:

| Tab | Name | Value |
|---|---|---|
| Secrets | `ANTHROPIC_API_KEY` | your Claude API key |
| Secrets | `NTFY_TOPIC` | your topic name |
| Variables | `SITE_URL` | `https://raulnech.github.io/dailydigest/` |

### 6. Test it
Repo → **Actions → Daily digest → Run workflow**. In 2–3 minutes you should get a notification. After that it runs every morning at 05:30 UTC (06:30 UK summer time). Change the `cron` line in `.github/workflows/daily.yml` to move it.

### 7. Put it on your home screen
Open the digest link on your phone → Share → **Add to Home Screen**. It opens like an app and always shows the latest digest.

## Running it on your own computer

```bash
pip install -r requirements.txt
python main.py --sample          # preview the page with sample data, no API key needed
```

Then open `docs/index.html`. For a real run, set `ANTHROPIC_API_KEY` (and optionally `NTFY_TOPIC`) and run `python main.py`.

## Customising

Everything is in `brief/config.py`: the model, timezone, how many stories per section, and the RSS feeds. The instructions Claude follows (what counts as important, how to explain things) are the `SYSTEM_PROMPT` in `brief/summarise.py`.

## Limitations

Claude writes from headlines and RSS snippets, not full articles (many are paywalled), and is told not to add facts that aren't in them. Still check the original before quoting a figure in an interview.
