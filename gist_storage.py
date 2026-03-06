"""
Stores sent article URLs in a GitHub Gist as JSON.
Used instead of SQLite since GitHub Actions has no persistent filesystem.
"""

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GIST_FILENAME = "sent_articles.json"
MAX_URLS = 500  # keep last N URLs to avoid infinite growth


def _gist_request(method: str, data: dict = None) -> dict:
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers=headers, method=method, data=body)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def load_sent_urls() -> set[str]:
    """Load the set of already-sent URLs from Gist."""
    try:
        result = _gist_request("GET")
        content = result["files"][GIST_FILENAME]["content"]
        data = json.loads(content)
        return set(data.get("urls", []))
    except Exception as e:
        logger.warning(f"Could not load Gist (first run?): {e}")
        return set()


def save_sent_urls(urls: set[str]):
    """Save the updated set of sent URLs back to Gist."""
    # Keep only the last MAX_URLS to avoid bloat
    url_list = list(urls)[-MAX_URLS:]
    try:
        _gist_request("PATCH", {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps({"urls": url_list}, indent=2)
                }
            }
        })
        logger.info(f"✅ Gist updated: {len(url_list)} URLs stored")
    except Exception as e:
        logger.error(f"Failed to save Gist: {e}")
