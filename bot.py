import os
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

from database import init_db, is_already_sent, mark_as_sent, cleanup_old_entries
from rss_parser import fetch_articles
from ai_filter import filter_hot_articles

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "3"))

bot = Bot(token=TELEGRAM_BOT_TOKEN)


def format_message(article, score: int, reason: str, emoji: str) -> str:
    """Format a news article into a Telegram message."""
    stars = "⭐" * min(score // 2, 5)
    return (
        f"{emoji} <b>{article.title}</b>\n\n"
        f"📰 <i>{article.source}</i> {stars}\n"
        f"💡 {reason}\n\n"
        f'<a href="{article.url}">Read more →</a>'
    )


async def check_and_send_news():
    """Main job: fetch, filter, and send hot cinema news."""
    logger.info("🔍 Starting news check...")

    try:
        # Fetch articles from all RSS feeds
        articles = fetch_articles(max_per_source=15)
        logger.info(f"📦 Total fetched: {len(articles)} articles")

        # Filter out already sent
        new_articles = [a for a in articles if not is_already_sent(a.url)]
        logger.info(f"🆕 New articles: {len(new_articles)}")

        if not new_articles:
            logger.info("Nothing new to process.")
            return

        # AI scoring
        hot_articles = filter_hot_articles(new_articles)
        logger.info(f"🔥 Hot articles: {len(hot_articles)}")

        # Send to Telegram
        sent_count = 0
        for article, score, reason, emoji in hot_articles:
            try:
                message = format_message(article, score, reason, emoji)
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
                mark_as_sent(article.url, article.title, article.source)
                sent_count += 1
                logger.info(f"✉️ Sent: {article.title[:60]}")
                await asyncio.sleep(1)  # avoid Telegram rate limits

            except Exception as e:
                logger.error(f"Failed to send message: {e}")

        logger.info(f"✅ Done. Sent {sent_count} hot news items.")

        # Cleanup old DB entries once a day (roughly)
        cleanup_old_entries(days=30)

    except Exception as e:
        logger.error(f"Error in check_and_send_news: {e}")


async def send_startup_message():
    """Notify that the bot has started."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=(
                f"🎬 <b>Cinema News Bot started!</b>\n\n"
                f"🕐 Checking every <b>{CHECK_INTERVAL_HOURS}h</b>\n"
                f"📡 Sources: Deadline, Variety, THR, Collider, IndieWire, Screen Rant\n"
                f"🤖 AI filtering: enabled\n\n"
                f"Started at: {now}"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")


async def main():
    logger.info("🚀 Cinema News Bot is starting...")

    # Validate env vars
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    if not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID is not set")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY is not set")

    # Init DB
    init_db()
    logger.info("📂 Database initialized")

    # Send startup notification
    await send_startup_message()

    # Run once immediately on start
    await check_and_send_news()

    # Schedule recurring job
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_news,
        trigger="interval",
        hours=CHECK_INTERVAL_HOURS,
        id="news_check",
    )
    scheduler.start()
    logger.info(f"⏰ Scheduler started: every {CHECK_INTERVAL_HOURS} hours")

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
