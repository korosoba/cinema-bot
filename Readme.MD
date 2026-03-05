# 🎬 Cinema News Bot

Мониторит топовые англоязычные источники о кино и присылает горячие новости в Telegram через AI-фильтрацию.

**Запускается через GitHub Actions — бесплатно, без сервера.**

## Источники
Deadline · Variety · Hollywood Reporter · Collider · IndieWire · Screen Rant

---

## Установка — пошагово

### 1. Создай Telegram бота

1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot`
2. Придумай имя и username боту
3. Скопируй **токен** (вида `123456:ABC-DEF...`)

**Узнай Chat ID:**
- Личный чат: напиши [@userinfobot](https://t.me/userinfobot)
- Канал: добавь бота как администратора, отправь любое сообщение в канал, затем открой:
  `https://api.telegram.org/bot<TOKEN>/getUpdates` — найди `"chat":{"id": ...}`

---

### 2. Создай GitHub Gist

1. Зайди на [gist.github.com](https://gist.github.com)
2. Создай новый **secret gist**
3. Имя файла: `sent_articles.json`
4. Содержимое: `{"urls": []}`
5. Скопируй **ID гиста** из URL: `gist.github.com/username/`**`ЭТО_И_ЕСТЬ_ID`**

---

### 3. Создай GitHub Personal Access Token для Gist

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → отметь только scope **`gist`**
3. Скопируй токен

---

### 4. Добавь секреты в репозиторий

GitHub репо → Settings → Secrets and variables → Actions → **New repository secret**

| Secret | Значение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `TELEGRAM_CHAT_ID` | ID чата или канала |
| `GEMINI_API_KEY` | ключ с aistudio.google.com |
| `GIST_TOKEN` | Personal Access Token с доступом к gist |
| `GIST_ID` | ID твоего гиста |

---

### 5. Залей код на GitHub и активируй Actions

```bash
git init
git add .
git commit -m "cinema news bot"
git branch -M main
git remote add origin https://github.com/твой/репо.git
git push -u origin main
```

После пуша зайди в **Actions** → выбери workflow → **Run workflow** для первого теста.

---

## Настройка

В файле `.github/workflows/news_bot.yml` можно изменить:

```yaml
cron: "0 */3 * * *"   # каждые 3 часа. Каждые 6ч: "0 */6 * * *"
HOT_THRESHOLD: "6"    # порог важности 0-10. Выше = строже фильтр
```

---

## Формат сообщения в Telegram

```
🏆 Cate Blanchett to Star in New Guillermo del Toro Film

📰 Deadline  ⭐⭐⭐⭐
💡 Крупный кастинг ожидаемого авторского проекта

Читать полностью →
```
