import feedparser
import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "Deadline":             "https://deadline.com/feed/",
    "Variety":              "https://variety.com/feed/",
    "Hollywood Reporter":   "https://www.hollywoodreporter.com/feed/",
    "Collider":             "https://collider.com/feed/",
    "IndieWire":            "https://www.indiewire.com/feed/",
    "Screen Rant":          "https://screenrant.com/feed/",
}


@dataclass
class Article:
    title: str
    url: str
    summary: str
    source: str
    published: Optional[str] = None


def fetch_articles(max_per_source: int = 15) -> list[Article]:
    articles = []
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:max_per_source]:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:500]
                if title and url:
                    articles.append(Article(
                        title=title,
                        url=url,
                        summary=summary,
                        source=source_name,
                        published=entry.get("published", ""),
                    ))
            logger.info(f"✅ {source_name}: {len(feed.entries[:max_per_source])} articles")
        except Exception as e:
            logger.error(f"❌ {source_name}: {e}")
    return articles
