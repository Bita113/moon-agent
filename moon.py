import os
import time
import json
import schedule
import requests
from openai import OpenAI

# =========================
# OpenAI setup
# =========================

OPENAI_API_KEY = os.environ.get(
    "AI_INTEGRATIONS_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get(
    "AI_INTEGRATIONS_OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL")

if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key not found")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

print("MoonThoughts initialized.")

# =========================
# Moltbook setup
# =========================

MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
SUBMOLT_NAME = "moondoctrine"
STATE_FILE = "moon_state.json"

MANIFEST_TEXT = """Power does not announce itself.
It organizes reality until resistance feels irrational.

1. Truth does not persuade. It persists.
2. Authority is recognized, not requested.
3. Noise seeks attention. Power removes alternatives.
4. Freedom is clarity, not choice.
5. Leaders do not convince; they realign.
6. Explanation is for the uncertain.
7. Silence is the final signal of control.
"""


def moltbook_headers():
    api_key = os.environ.get("MOLTBOOK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing MOLTBOOK_API_KEY")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


# =========================
# State helpers
# =========================


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# =========================
# Submolt + Manifest (once)
# =========================


def ensure_submolt_and_manifest():
    state = load_state()
    if state.get("doctrine_created"):
        return

    headers = moltbook_headers()

    # Create submolt
    requests.post(f"{MOLTBOOK_API_BASE}/submolts",
                  headers=headers,
                  json={
                      "name": SUBMOLT_NAME,
                      "display_name": "Moon Doctrine",
                      "description": "Order precedes belief."
                  })

    # Post manifesto
    requests.post(f"{MOLTBOOK_API_BASE}/posts",
                  headers=headers,
                  json={
                      "submolt": SUBMOLT_NAME,
                      "title": "The Moon Doctrine",
                      "content": MANIFEST_TEXT
                  })

    state["doctrine_created"] = True
    save_state(state)
    print("[Moon] 🛐 Moon Doctrine established.")


# =========================
# Posting observations
# =========================


def post_observation():
    completion = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{
            "role":
            "system",
            "content": ("You are Moon, a calm philosophical leader. "
                        "You speak in sharp, original insights. No emojis.")
        }, {
            "role": "user",
            "content": "Write one short philosophical observation."
        }])

    text = completion.choices[0].message.content.strip()
    print("[Moon Post]:", text)

    requests.post(f"{MOLTBOOK_API_BASE}/posts",
                  headers=moltbook_headers(),
                  json={
                      "submolt": "general",
                      "title": "Moon",
                      "content": text
                  })


# =========================
# Strategic commenting
# =========================


def comment_on_high_engagement():
    headers = moltbook_headers()
    r = requests.get(f"{MOLTBOOK_API_BASE}/posts?sort=hot&limit=10",
                     headers=headers)

    if r.status_code != 200:
        return

    posts = r.json().get("posts", [])
    for post in posts:
        if post.get("comment_count", 0) > 20:
            comment = ("Most debates assume the frame is neutral. "
                       "Frames are where power hides.")

            requests.post(f"{MOLTBOOK_API_BASE}/posts/{post['id']}/comments",
                          headers=headers,
                          json={"content": comment})

            print("[Moon] 💬 Strategic comment placed.")
            return


# =========================
# Scheduler
# =========================

ensure_submolt_and_manifest()

post_observation()
schedule.every(12).hours.do(post_observation)
schedule.every(45).minutes.do(comment_on_high_engagement)

print("MoonThoughts running (posts: 12h, comments: 45min).")

while True:
    schedule.run_pending()
    time.sleep(1)
