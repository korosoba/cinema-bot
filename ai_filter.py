import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ["GROQ_API_KEY"])
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))

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

    lines = [f"{i}. [{a.source}] {a.title}" for i, a in enumerate(articles, 1)]
    user_prompt = "\n".join(lines)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(raw)
        score_map = {item["id"]: item for item in scores}

    except Exception as e:
        logger.error(f"Groq eval failed: {e}")
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
