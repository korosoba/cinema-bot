"""
Main entry point for GitHub Actions.
No scheduler needed — Actions triggers this script on cron.
"""

import os
import time
import logging
import urllib.request
import urllib.parse
import json

from gist_storage import load_sent_urls, save_sent_urls
from rss_parser import fetch_articles
from ai_filter import filter_hot_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def format_message(article, score: int, reason: str, emoji: str) -> str:
    stars = "⭐" * min(score // 2, 5)
    return (
        f"{emoji} <b>{article.title}</b>\n\n"
        f"📰 <i>{article.source}</i>  {stars}\n"
        f"💡 {reason}\n\n"
        f'<a href="{article.url}">Читать полностью →</a>'
    )


def main():
    logger.info("🚀 Cinema News Bot starting...")

    # Load already-sent URLs from Gist
    sent_urls = load_sent_urls()
    logger.info(f"📂 Loaded {len(sent_urls)} sent URLs from Gist")

    # Fetch all articles
    articles = fetch_articles(max_per_source=15)
    logger.info(f"📦 Fetched {len(articles)} total articles")

    # Filter out duplicates
    new_articles = [a for a in articles if a.url not in sent_urls]
    logger.info(f"🆕 New articles: {len(new_articles)}")

    if not new_articles:
        logger.info("Nothing new. Exiting.")
        return

    # AI scoring
    hot = filter_hot_articles(new_articles)
    logger.info(f"🔥 Hot articles: {len(hot)}")

    # Send to Telegram
    sent_count = 0
    for article, score, reason, emoji in hot:
        try:
            send_telegram(format_message(article, score, reason, emoji))
            sent_urls.add(article.url)
            sent_count += 1
            logger.info(f"✉️  Sent: {article.title[:70]}")
            time.sleep(1)  # avoid Telegram rate limit
        except Exception as e:
            logger.error(f"Failed to send: {e}")

    logger.info(f"✅ Done. Sent {sent_count} articles.")

    # Save updated URL list back to Gist
    save_sent_urls(sent_urls)


if __name__ == "__main__":
    main()
