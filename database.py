import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "cinema_bot.db")


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            source TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_already_sent(url: str) -> bool:
    """Check if an article has already been sent."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_articles WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_as_sent(url: str, title: str, source: str):
    """Mark an article as sent."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO sent_articles (url, title, source) VALUES (?, ?, ?)",
            (url, title, source)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already exists
    finally:
        conn.close()


def cleanup_old_entries(days: int = 30):
    """Remove entries older than specified days to keep DB small."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM sent_articles WHERE sent_at < datetime('now', ? || ' days')",
        (f"-{days}",)
    )
    conn.commit()
    conn.close()
