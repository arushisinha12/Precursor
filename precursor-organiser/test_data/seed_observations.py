"""
Loops through test_data/synthetic_observations.json and POSTs each entry to
the running backend's real POST /observations/ endpoint.

Run this BEFORE the demo, not during it — each POST with a photo triggers a
real synchronous Gemini call (see routes/observations.py's create_observation),
and the model is rate-limited. Seeding 35 observations will take a while;
budget a few minutes, not seconds.

Usage:
    python3 seed_observations.py
    python3 seed_observations.py --url http://localhost:8000
    python3 seed_observations.py --file synthetic_observations.json --delay 1.5
"""

import argparse
import json
import time
from pathlib import Path

import requests

# Fields backend's ObservationCreate actually accepts (schemas.py).
# Anything else on each record (timestamp, _category_hint) is stripped
# before sending — backend ignores unknown fields anyway, but stripping
# explicitly here makes it obvious what's actually part of the contract.
ALLOWED_FIELDS = {"user_id", "description", "photo_url", "latitude", "longitude"}


def load_observations(path):
    with open(path, "r") as f:
        return json.load(f)


def to_payload(record):
    return {key: record.get(key) for key in ALLOWED_FIELDS}


def seed(base_url, file_path, delay_seconds):
    observations = load_observations(file_path)
    endpoint = f"{base_url.rstrip('/')}/observations/"

    succeeded = 0
    failed = 0

    for index, record in enumerate(observations, start=1):
        payload = to_payload(record)
        has_photo = bool(payload.get("photo_url"))

        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            succeeded += 1
            tag_hint = record.get("_category_hint", "?")
            print(f"[{index}/{len(observations)}] OK  ({tag_hint}{', photo' if has_photo else ''})")
        except requests.RequestException as e:
            failed += 1
            print(f"[{index}/{len(observations)}] FAILED: {e}")

        # Space out requests, mainly so photo-bearing ones (real Gemini
        # vision calls) don't stack up against the rate limit. Text-only
        # calls are cheap enough that this delay is mostly slack for those.
        if index < len(observations):
            time.sleep(delay_seconds)

    print(f"\nDone. {succeeded} succeeded, {failed} failed, out of {len(observations)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the backend with synthetic observations.")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--file", default="synthetic_observations.json", help="Path to the generated JSON file")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds to wait between POSTs")
    args = parser.parse_args()

    seed(base_url=args.url, file_path=Path(args.file), delay_seconds=args.delay)
