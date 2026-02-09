import os
import json
import requests
from openai import OpenAI

# =========================
# OpenAI setup
# =========================

OPENAI_API_KEY = (
    os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
)

OPENAI_BASE_URL = (
    os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    or os.environ.get("OPENAI_BASE_URL")
)

if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key not found")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

print("Moon agent started.")

# =========================
# Generate thought
# =========================

prompt = (
    "Generate ONE short, sharp, non-generic philosophical observation "
    "about life, power, money, or AI. No emojis. Max 2 sentences."
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.8,
)

thought = response.choices[0].message.content.strip()

print("Generated thought:")
print(thought)

# =========================
# (Optional) save locally
# =========================

state = {
    "last_thought": thought
}

with open("moon_state.json", "w") as f:
    json.dump(state, f, indent=2)

print("Moon agent finished successfully.")
