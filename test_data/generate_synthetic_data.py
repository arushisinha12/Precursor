import json
import random
import base64
from datetime import datetime, timedelta
from sample_categories import CATEGORY_DESCRIPTIONS

# Fake campus locations to cluster observations around
LOCATIONS = [
    {"name": "Block C Staircase", "lat": 12.9353, "lng": 77.6246},
    {"name": "Library Entrance", "lat": 12.9358, "lng": 77.6251},
    {"name": "Canteen", "lat": 12.9349, "lng": 77.6244},
    {"name": "Gym", "lat": 12.9361, "lng": 77.6238},
]

FAKE_USERS = [f"user{i}" for i in range(1, 16)]  # 15 fake users


def encode_image_to_data_uri(image_path):
    """
    Returns a full "data:image/<ext>;base64,<data>" string, since that's what
    backend's load_image_from_data_uri() expects (it splits on the first comma
    to strip the header). Raw base64 with no prefix would break that parsing.
    """
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext  # jpg -> jpeg is the only real mismatch

    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/{mime};base64,{encoded}"
    except FileNotFoundError:
        return None


def random_offset():
    # Small offset so points scatter near a location, not stacked exactly
    return random.uniform(-0.0006, 0.0006)


def random_timestamp(max_days_ago=3):
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, max_days_ago),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return (now - delta).isoformat()


def generate_random_observation():
    category = random.choice(list(CATEGORY_DESCRIPTIONS.keys()))
    description = random.choice(CATEGORY_DESCRIPTIONS[category])
    location = random.choice(LOCATIONS)

    return {
        "user_id": random.choice(FAKE_USERS),
        "description": description,
        # NOTE: backend's ObservationCreate has no "timestamp" field — it's
        # server-generated at insert time (func.now() in models.py). This
        # value is kept here for your own reference/sorting only; the
        # seeding script below strips it before POSTing, since sending it
        # would just be silently ignored by the backend anyway.
        "photo_url": None,
        "latitude": location["lat"] + random_offset(),
        "longitude": location["lng"] + random_offset(),
        "timestamp": random_timestamp(),
        "_category_hint": category  # for your own reference, remove before sending to backend if needed
    }


def generate_intentional_cluster(location, category, count=5):
    """Generates a tight cluster of related reports at one location, recent timestamps,
    guaranteed to demo the emergence detection working."""
    observations = []
    descriptions = CATEGORY_DESCRIPTIONS[category]

    # Attach a real photo to the first report for demo authenticity
    # Adjust the path below to match wherever your sample images actually live
    photo_data_uri = encode_image_to_data_uri("sample_images/dim_light.jpg")

    for i in range(count):
        observations.append({
            "user_id": FAKE_USERS[i % len(FAKE_USERS)],
            "description": random.choice(descriptions),
            "photo_url": photo_data_uri if i == 0 else None,
            "latitude": location["lat"] + random_offset(),
            "longitude": location["lng"] + random_offset(),
            "timestamp": random_timestamp(max_days_ago=0),  # all recent
            "_category_hint": category
        })
    return observations


def generate_dataset(background_count=30):
    dataset = []

    # Background noise — scattered, random, mostly low-stakes
    for _ in range(background_count):
        dataset.append(generate_random_observation())

    # One intentional cluster for guaranteed demo moment
    cluster_location = LOCATIONS[0]  # Block C Staircase
    dataset.extend(generate_intentional_cluster(cluster_location, "lighting", count=5))

    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    data = generate_dataset(background_count=30)
    with open("synthetic_observations.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} synthetic observations -> synthetic_observations.json")