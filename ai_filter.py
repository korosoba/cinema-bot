import os
import json
import logging
import time
import urllib.request

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)

SYSTEM_PROMPT = """You are a cinema news editor for a Telegram channel.
Evaluate if a news article is important/breaking enough to notify subscribers.

Score 0–10:
- 8-10: Truly breaking — major casting, Oscar winners, record box office, franchise announcements
- 6-7: Notable — trailer drops, festival buzz, director announcements, sequels confirmed
- 3-5: Routine — interviews, reviews, minor updates
- 0-2: Filler — listicles, opinion pieces, clickbait

Reply ONLY with valid JSON, no markdown, no extra text:
{"score": <0-10>, "reason": "<one sentence in Russian>", "emoji": "<one emoji>"}"""


def evaluate_article(article) -> tuple[int, str, str]:
    prompt = f"{SYSTEM_PROMPT}\n\nSource: {article.source}\nTitle: {article.title}\nSummary: {article.summary[:300]}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 150, "temperature": 0.2},
    }).encode()

    try:
        req = urllib.request.Request(
            GEMINI_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        time.sleep(5)  # max 15 req/min on free tier → 1 req per 4s, we use 5s to be safe

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip markdown fences if Gemini adds them
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
        return int(result.get("score", 0)), result.get("reason", ""), result.get("emoji", "🎬")

    except Exception as e:
        logger.error(f"Gemini eval failed for '{article.title[:50]}': {e}")
        return 0, "", "🎬"


def filter_hot_articles(articles) -> list[tuple]:
    results = []
    for article in articles:
        score, reason, emoji = evaluate_article(article)
        logger.info(f"[{score}/10] {article.source} | {article.title[:60]}")
        if score >= HOT_THRESHOLD:
            results.append((article, score, reason, emoji))
    return sorted(results, key=lambda x: x[1], reverse=True)
