# 🎬 Cinema News Bot

Telegram bot that monitors top English cinema news sources and sends hot breaking news using AI filtering.

## Sources
- Deadline
- Variety  
- The Hollywood Reporter
- Collider
- IndieWire
- Screen Rant

## How it works
1. Every N hours fetches latest articles from RSS feeds
2. Filters out already-sent articles (SQLite)
3. Claude AI scores each article 0–10 for importance
4. Articles scoring ≥ threshold are sent to your Telegram chat

---

## Setup

### 1. Get your tokens

**Telegram Bot Token:**
1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot`, follow instructions
3. Copy the token

**Telegram Chat ID:**
- For a personal chat: message [@userinfobot](https://t.me/userinfobot)
- For a channel: add your bot as admin, then send a message and check:
  `https://api.telegram.org/bot<TOKEN>/getUpdates`

**Anthropic API Key:**
- Go to [console.anthropic.com](https://console.anthropic.com)
- Create an API key

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Run locally

```bash
pip install -r requirements.txt
python bot.py
```

---

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render will detect `render.yaml` automatically
5. Add your environment variables in Render dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `ANTHROPIC_API_KEY`
6. Deploy!

> **Note:** Use Render's **Worker** service type (not Web Service) — the bot doesn't need HTTP.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CHECK_INTERVAL_HOURS` | `3` | How often to check news |
| `HOT_THRESHOLD` | `6` | Min AI score (0–10) to send |

Tune `HOT_THRESHOLD`:
- `5` — more news, including medium stories
- `6` — balanced (recommended)
- `8` — only truly breaking news
