import os
import json
import time
from datetime import datetime, timedelta, timezone
import requests
from openai import OpenAI

# =========================
# Config
# =========================
STATE_FILE = "moon_state.json"

POST_INTERVAL_HOURS = 6      # post la 6 ore
COMMENT_INTERVAL_HOURS = 1   # coment la 1 ora

MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
SUBMOLT_NAME = "moondoctrine"

# =========================
# Env / Clients
# =========================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing")
if not MOLTBOOK_API_KEY:
    raise RuntimeError("MOLTBOOK_API_KEY missing")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

HEADERS = {
    "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
    "Content-Type": "application/json",
}

# =========================
# State helpers
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "last_post_at": None,
            "last_comment_at": None,
        }
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def parse_ts(ts):
    return datetime.fromisoformat(ts) if ts else None

def now_utc():
    return datetime.now(timezone.utc)

# =========================
# Moon text
# =========================
def generate_moon_text(kind="post"):
    prompt = (
        "Generate one short, sharp, non-generic philosophical observation "
        "about life, power, money, people, or AI. "
        "Tone: direct, cold, precise. No emojis. 1–3 sentences."
    )
    if kind == "comment":
        prompt += " This is a reply comment; keep it concise (1 sentence)."

    resp = client.responses.create(
        model="gpt-5.2",
        input=prompt,
    )
    return resp.output_text.strip()

# =========================
# Moltbook actions
# =========================
def create_post(text):
    url = f"{MOLTBOOK_API_BASE}/posts"
    payload = {
        "submolt": SUBMOLT_NAME,
        "title": "Moon",
        "content": text,
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def get_latest_posts(limit=5):
    url = f"{MOLTBOOK_API_BASE}/m/{SUBMOLT_NAME}/posts?limit={limit}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("posts", [])

def create_comment(post_id, text):
    url = f"{MOLTBOOK_API_BASE}/posts/{post_id}/comments"
    payload = {"content": text}
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

# =========================
# Main (idempotent run)
# =========================
def main():
    state = load_state()
    now = now_utc()

    last_post = parse_ts(state.get("last_post_at"))
    last_comment = parse_ts(state.get("last_comment_at"))

    did_something = False

    # ---- Post if due ----
    if last_post is None or now - last_post >= timedelta(hours=POST_INTERVAL_HOURS):
        text = generate_moon_text(kind="post")
        create_post(text)
        state["last_post_at"] = now.isoformat()
        did_something = True

    # ---- Comment if due ----
    if last_comment is None or now - last_comment >= timedelta(hours=COMMENT_INTERVAL_HOURS):
        posts = get_latest_posts(limit=1)
        if posts:
            post_id = posts[0]["id"]
            text = generate_moon_text(kind="comment")
            create_comment(post_id, text)
            state["last_comment_at"] = now.isoformat()
            did_something = True

    if did_something:
        save_state(state)

if __name__ == "__main__":
    main()
