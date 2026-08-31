import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HOT_THRESHOLD = int(os.getenv("HOT_THRESHOLD", "6"))
BATCH_SIZE = 10  # статей за один запрос

SYSTEM_PROMPT = """Ты — редактор Telegram-канала о кино. Получаешь список новостей из русских и английских источников.

Оцени каждую новость от 0 до 10 по важности для киноаудитории:
- 8–10: Топ-новость — крупный кастинг, победители Оскара/Каннов/Венеции, рекорды кассовых сборов, анонс крупной франшизы (Marvel, DC, Star Wars и т.д.), скандалы уровня индустрии
- 6–7: Заметная новость — выход трейлера ожидаемого фильма, подтверждение сиквела, назначение режиссёра на громкий проект, фестивальные премьеры, крупные российские релизы
- 3–5: Рядовая новость — интервью, рецензии, даты выхода второстепенных фильмов, ТВ-новости
- 0–2: Неважно — listicles, мнения, кликбейт, новости сериалов без явной кинозначимости

Ответь ТОЛЬКО валидным JSON-массивом, без markdown, без лишнего текста:
[{"id": 1, "score": 8, "reason": "одно предложение на русском — почему важно", "emoji": "🎬"}, ...]"""


def call_groq(lines: list[str], id_offset: int) -> list[dict]:
    """Отправляет батч статей в Groq и возвращает список оценок."""
    numbered = [f"{id_offset + i}. {line}" for i, line in enumerate(lines)]
    user_prompt = "\n".join(numbered)

    payload = json.dumps({
        "model": "qwen/qwen3.6-27b",
        "temperature": 0.2,
        "max_tokens": 2048,
        "reasoning_effort": "none",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }).encode()

    req = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "User-Agent": "Mozilla/5.0",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"].strip()

    # Ищем JSON-массив
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        logger.error(f"JSON-массив не найден: {raw[:200]}")
        return []

    return json.loads(raw[start:end])


def filter_hot_articles(articles) -> list[tuple]:
    if not articles:
        return []

    score_map = {}
    lines = [f"[{a.source}] {a.title}" for a in articles]

    # Обрабатываем батчами
    for batch_start in range(0, len(lines), BATCH_SIZE):
        batch = lines[batch_start:batch_start + BATCH_SIZE]
        id_offset = batch_start + 1
        try:
            scores = call_groq(batch, id_offset)
            for item in scores:
                score_map[item["id"]] = item
            logger.info(f"Батч {batch_start//BATCH_SIZE + 1}: оценено {len(scores)} статей")
        except Exception as e:
            logger.error(f"Groq eval failed (батч {batch_start//BATCH_SIZE + 1}): {e}")

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
