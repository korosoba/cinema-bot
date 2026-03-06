import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)

SYSTEM_PROMPT = """You are a cinema news editor for a Telegram channel.
You will receive a numbered list of news article titles and sources.
Score each one from 0-10 based on importance:

- 8-10: Truly breaking - major casting, Oscar winners, record box office, franchise announcements
- 6-7: Notable - trailer drops, festival buzz, director announcements, sequels confirmed
- 3-5: Routine - interviews, reviews, minor updates
- 0-2: Filler - listicles, opinion pieces, clickbait

Reply ONLY with a valid JSON array, one object per article, no markdown, no extra text:
[{"id": 1, "score": 8, "reason": "одно предложение на русском", "emoji": "🎬"}, ...]"""


def filter_hot_articles(articles) -> list[tuple]:
    if not articles:
        return []

    # Build numbered list for a single batch prompt
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. [{a.source}] {a.title}")
    prompt = SYSTEM_PROMPT + "\n\n" + "\n".join(lines)

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.2},
    }).encode()

    try:
        req = urllib.request.Request(
            GEMINI_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(raw)
        score_map = {item["id"]: item for item in scores}

    except Exception as e:
        logger.error(f"Gemini batch eval failed: {e}")
        return []

    results = []
    for i, article in enumerate(articles, 1):
        item = score_map.get(i, {})
        score = int(item.get("score", 0))
        reason = item.get("reason", "")
        emoji = item.get("emoji", "🎬")
        logger.info(f"[{score}/10] {article.source} | {article.title[:60]}")
        if score >= HOT_THRESHOLD:
            results.append((article, score, reason, emoji))

    return sorted(results, key=lambda x: x[1], reverse=True)
