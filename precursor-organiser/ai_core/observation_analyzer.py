import base64
import json
import re
from io import BytesIO

import requests
from PIL import Image

from ai_config import AI_ENABLED, GEMINI_API_KEY, MODEL_NAME
from ai_core.schema import ALLOWED_TAGS, SEVERITY_SCALE

model = None
if AI_ENABLED:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)


def build_prompt(observation_text):
    tags_list = ", ".join(ALLOWED_TAGS)
    severity_lines = "\n".join([f"{k} = {v}" for k, v in SEVERITY_SCALE.items()])

    prompt = f"""
You are analyzing a short observation report about a physical space (e.g. a campus building).

Observation text: "{observation_text}"

Your task:
1. Pick one or more relevant tags ONLY from this fixed list: {tags_list}
2. Assign a severity score from 1 to 5 using this scale:
{severity_lines}

If an image is attached, use it together with the text to judge severity and confirm tags.

Return ONLY valid JSON in exactly this format, with no extra text, no markdown, no explanation:
{{"tags": ["tag1", "tag2"], "severity": 3}}
"""
    return prompt.strip()


def parse_response(raw_text):
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        data = json.loads(cleaned)
        tags = [t for t in data.get("tags", []) if t in ALLOWED_TAGS]
        severity = int(data.get("severity", 1))
        severity = max(1, min(5, severity))
        return {"tags": tags, "severity": severity}
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"tags": ["other"], "severity": 3, "needs_review": True}


def load_image_from_url(photo_url):
    response = requests.get(photo_url, timeout=10)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))


def load_image_from_data_uri(data_uri):
    # e.g. "data:image/png;base64,iVBORw0KGgo..." - frontend sends photos
    # this way instead of a hosted URL, since there's no image-hosting step
    # in this project. Avoids a network fetch (and a third-party dependency)
    # entirely, which also makes the demo not depend on an external service
    # being up.
    header, encoded = data_uri.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    return Image.open(BytesIO(image_bytes))


def load_image(photo_url):
    if photo_url.startswith("data:image"):
        return load_image_from_data_uri(photo_url)
    return load_image_from_url(photo_url)


# --- Offline fallback analyzer -------------------------------------------
# Used automatically whenever GEMINI_API_KEY isn't configured, so the
# prototype is fully usable without any API key. Does simple keyword
# matching against ALLOWED_TAGS plus a couple of severity-signal words.
# It's intentionally simple - swap in a real GEMINI_API_KEY in backend/.env
# any time to get real model-based analysis instead.
KEYWORD_TAGS = {
    "lighting": ["light", "lamp", "bulb", "flicker", "dark", "dim"],
    "electrical": ["wire", "wiring", "cable", "spark", "outlet", "electric", "shock", "switchboard"],
    "water": ["water", "leak", "puddle", "damp", "wet", "flood"],
    "plumbing": ["toilet", "sink", "drain", "pipe", "faucet", "tap", "clog"],
    "structural": ["crack", "ceiling", "wall", "handrail", "railing", "beam", "collapse", "wobbly"],
    "cleanliness": ["trash", "litter", "dirty", "dust", "garbage", "mess"],
    "overflow": ["overflow", "overflowing", "spilling"],
    "accessibility": ["ramp", "wheelchair", "accessib", "elevator", "lift"],
    "crowding": ["crowd", "crowded", "packed", "queue", "line"],
    "equipment": ["equipment", "machine", "broken", "malfunction"],
    "safety": ["danger", "hazard", "unsafe", "injur", "fire", "smoke"],
}

SEVERE_WORDS = ["immediate", "urgent", "critical", "danger", "fire", "smoke", "shock", "collapse", "injur"]
MINOR_WORDS = ["small", "minor", "slight", "little"]


def analyze_observation_offline(description):
    text = description.lower()
    tags = []
    for tag, keywords in KEYWORD_TAGS.items():
        if any(re.search(keyword, text) for keyword in keywords):
            tags.append(tag)

    if not tags:
        tags = ["other"]

    severity = 3
    if any(word in text for word in SEVERE_WORDS):
        severity = 5
    elif any(word in text for word in MINOR_WORDS):
        severity = 2

    return {"tags": tags, "severity": severity}


def analyze_observation(description, photo_url=None):
    if not AI_ENABLED:
        # No Gemini key configured - use the offline keyword-based fallback
        # so the app is fully functional without any external API key.
        return analyze_observation_offline(description)

    prompt = build_prompt(description)

    if photo_url:
        try:
            image = load_image(photo_url)
            response = model.generate_content([prompt, image])
        except Exception as e:
            print(f"Could not load image, falling back to text-only. Error: {e}")
            response = model.generate_content(prompt)
    else:
        response = model.generate_content(prompt)

    return parse_response(response.text)


if __name__ == "__main__":
    result = analyze_observation(
        "Something looks off here.",
        photo_url="https://i.postimg.cc/9XpkhQJR/test-data-sample-images-damaged-wire.png"
    )
    print(result)
