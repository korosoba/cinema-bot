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
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")


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


def publish_to_vk(article, score: int, reason: str, emoji: str):
    """Публикует горячую новость отдельным постом в VK-группу."""
    if not VK_TOKEN or not VK_GROUP_ID:
        return

    stars = "⭐" * min(score // 2, 5)
    text = (
        f"{emoji} {article.title}\n\n"
        f"📰 {article.source}  {stars}\n"
        f"💡 {reason}\n\n"
        f"🔗 {article.url}"
    )

    try:
        params = urllib.parse.urlencode({
            "owner_id": f"-{VK_GROUP_ID}",
            "message": text[:4096],
            "access_token": VK_TOKEN,
            "v": "5.199",
        }).encode()
        req = urllib.request.Request(
            "https://api.vk.com/method/wall.post",
            data=params
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if "error" in result:
                logger.error(f"VK error: {result['error']}")
            else:
                logger.info(f"✅ VK: пост опубликован ({result.get('response', {}).get('post_id')})")
    except Exception as e:
        logger.error(f"VK publish failed: {e}")


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

    sent_urls = load_sent_urls()
    logger.info(f"📂 Loaded {len(sent_urls)} sent URLs from Gist")

    articles = fetch_articles(max_per_source=15)
    logger.info(f"📦 Fetched {len(articles)} total articles")

    new_articles = [a for a in articles if a.url not in sent_urls]
    logger.info(f"🆕 New articles: {len(new_articles)}")

    if not new_articles:
        logger.info("Nothing new. Exiting.")
        return

    hot = filter_hot_articles(new_articles)
    logger.info(f"🔥 Hot articles: {len(hot)}")

    sent_count = 0
    for article, score, reason, emoji in hot:
        try:
            send_telegram(format_message(article, score, reason, emoji))
            sent_urls.add(article.url)
            sent_count += 1
            logger.info(f"✉️  Sent: {article.title[:70]}")

            # Дублируем в VK
            publish_to_vk(article, score, reason, emoji)

            time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send: {e}")

    logger.info(f"✅ Done. Sent {sent_count} articles.")
    save_sent_urls(sent_urls)


if __name__ == "__main__":
    main()
