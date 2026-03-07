import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ["GROQ_API_KEY"])
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))

SYSTEM_PROMPT = """Ты — редактор Telegram-канала о кино. Получаешь список новостей из русских и английских источников.

Оцени каждую новость от 0 до 10 по важности для киноаудитории:

- 8–10: Топ-новость — крупный кастинг, победители Оскара/Каннов/Венеции, рекорды кассовых сборов, анонс крупной франшизы (Marvel, DC, Star Wars и т.д.), скандалы уровня индустрии
- 6–7: Заметная новость — выход трейлера ожидаемого фильма, подтверждение сиквела, назначение режиссёра на громкий проект, фестивальные премьеры, крупные российские релизы
- 3–5: Рядовая новость — интервью, рецензии, даты выхода второстепенных фильмов, ТВ-новости
- 0–2: Неважно — listicles, мнения, кликбейт, новости сериалов без явной кинозначимости

Дополнительно учитывай:
- Для русскоязычных источников: новости о российском прокате, отечественных фильмах и фестивалях могут быть актуальнее
- Для англоязычных: голливудские новости, крупные студии, мировые сборы

Ответь ТОЛЬКО валидным JSON-массивом, без markdown, без лишнего текста:
[{"id": 1, "score": 8, "reason": "одно предложение на русском — почему важно", "emoji": "🎬"}, ...]"""


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
