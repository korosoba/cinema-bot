import os
import json
import logging
import anthropic
from rss_parser import Article

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Minimum score to consider a news item "hot" (0-10)
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))

SYSTEM_PROMPT = """You are an expert cinema news editor for a popular Telegram channel about movies.
Your job is to evaluate whether a news article is "hot" or important enough to notify subscribers.

Rate the article on a scale from 0 to 10 based on:
- Breaking news about major films or franchises (Marvel, DC, Star Wars, etc.) → high score
- Oscar news, major awards, box office records → high score  
- Big casting announcements, director changes → high score
- Trailer releases for anticipated films → high score
- Festival premieres (Cannes, Venice, Sundance) → medium-high score
- Minor interviews, listicles, opinion pieces → low score
- Clickbait or non-essential content → very low score

Respond ONLY with a valid JSON object, no markdown, no extra text:
{"score": <0-10>, "reason": "<one sentence why>", "emoji": "<one relevant emoji>"}"""


def evaluate_article(article: Article) -> tuple[int, str, str]:
    """
    Use Claude to evaluate if an article is hot news.
    Returns (score, reason, emoji).
    """
    try:
        prompt = f"""Source: {article.source}
Title: {article.title}
Summary: {article.summary[:300]}

Rate this cinema news article."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        data = json.loads(raw)

        score = int(data.get("score", 0))
        reason = data.get("reason", "")
        emoji = data.get("emoji", "🎬")

        return score, reason, emoji

    except Exception as e:
        logger.error(f"AI evaluation failed for '{article.title}': {e}")
        return 0, "Evaluation failed", "🎬"


def filter_hot_articles(articles: list[Article]) -> list[tuple[Article, int, str, str]]:
    """
    Filter articles by AI score. Returns list of (article, score, reason, emoji)
    sorted by score descending.
    """
    results = []

    for article in articles:
        score, reason, emoji = evaluate_article(article)
        logger.info(f"Score {score}/10 | {article.source} | {article.title[:60]}")

        if score >= HOT_THRESHOLD:
            results.append((article, score, reason, emoji))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results
