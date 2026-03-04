import feedparser
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Top English cinema news RSS feeds
RSS_FEEDS = {
    "Deadline": "https://deadline.com/feed/",
    "Variety": "https://variety.com/feed/",
    "Hollywood Reporter": "https://www.hollywoodreporter.com/feed/",
    "Collider": "https://collider.com/feed/",
    "IndieWire": "https://www.indiewire.com/feed/",
    "Screen Rant": "https://screenrant.com/feed/",
}


@dataclass
class Article:
    title: str
    url: str
    summary: str
    source: str
    published: Optional[str] = None


def fetch_articles(max_per_source: int = 10) -> list[Article]:
    """Fetch latest articles from all RSS feeds."""
    articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:max_per_source]

            for entry in entries:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                published = entry.get("published", "")

                # Clean up HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary)
                summary = summary[:500]  # limit length

                if title and url:
                    articles.append(Article(
                        title=title,
                        url=url,
                        summary=summary,
                        source=source_name,
                        published=published,
                    ))

            logger.info(f"✅ {source_name}: fetched {len(entries)} articles")

        except Exception as e:
            logger.error(f"❌ Failed to fetch {source_name}: {e}")

    return articles
