"""
Seeds the local SQLite DB with a small, hand-picked set of observations so
the map shows real clusters in all three statuses (red/yellow/green) without
depending on the Gemini API at all — tags and severity are set directly here,
the same way the AI step normally would, then run through the *real*
update_cluster() so the clustering/scoring logic is exercised exactly as it
is in production.

Run from the precursor-backend-final (or precursor) folder:
    python -m test_data.seed_demo_data

Safe to re-run — it just adds more rows / clusters each time.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, engine
from models import Base, Observation
from services.clustering import update_cluster

Base.metadata.create_all(bind=engine)

# Centered near the map's default fallback location. Points inside a group
# are ~10-30m apart (well under the 100m clustering radius); the three
# groups are spaced ~500m+ apart so they never merge into each other.
BASE_LAT, BASE_LON = 12.9351, 77.6054

# (lat_offset, lon_offset, user_id, description, tags, severity)
# Score = observation_count x distinct_users x average_severity x recency
# Recency is 1.0 for anything inserted in the last hour, which freshly
# seeded rows always are.
SEED_ROWS = [
    # --- Cluster A: RED --------------------------------------------------
    # 4 observations, 3 distinct users, severity 5 avg -> 4 x 3 x 5 x 1.0 = 60 (> 50 -> red)
    (0.0000, 0.0000, "user_1", "Flickering light near the stairwell, feels dangerous at night", ["lighting", "safety"], 5),
    (0.0001, 0.0001, "user_2", "Same stairwell light still flickering, real safety hazard", ["lighting", "safety"], 5),
    (0.0001, -0.0001, "user_3", "Stairwell light out again, dangerous in the dark", ["lighting", "safety"], 5),
    (-0.0001, 0.0002, "user_1", "Flickering light hasn't been fixed, immediate hazard", ["lighting", "safety"], 5),

    # --- Cluster B: YELLOW -------------------------------------------------
    # 3 observations, 2 distinct users, severity 4 avg -> 3 x 2 x 4 x 1.0 = 24 (20-50 -> yellow)
    (0.0045, 0.0045, "user_4", "Small water leak near the water fountain", ["water", "plumbing"], 4),
    (0.0046, 0.0044, "user_5", "Water leak still there, puddle getting bigger", ["water", "plumbing"], 4),
    (0.0044, 0.0046, "user_4", "Leak by the fountain again, floor is wet", ["water", "plumbing"], 4),

    # --- Isolated report: no cluster forms (only 1 report) -----------------
    # Deliberately alone -> shows a single green marker with no alert, to
    # contrast against the two clusters above ("one report isn't a pattern yet").
    (-0.0090, -0.0060, "user_6", "A bit of litter near the entrance, nothing urgent", ["cleanliness"], 2),
]


def seed():
    db = SessionLocal()
    try:
        created = []
        for lat_off, lon_off, user_id, description, tags, severity in SEED_ROWS:
            obs = Observation(
                user_id=user_id,
                description=description,
                photo_url=None,
                latitude=BASE_LAT + lat_off,
                longitude=BASE_LON + lon_off,
            )
            db.add(obs)
            db.commit()
            db.refresh(obs)

            # Set tags/severity directly instead of calling analyze_observation()
            # - this is what the AI step would normally fill in, but doing it
            # here means seeding never depends on GEMINI_API_KEY or network.
            obs.tags = tags
            obs.severity = severity
            obs.needs_review = False
            db.commit()
            db.refresh(obs)

            update_cluster(obs, db)
            created.append(obs.id)

        print(f"Seeded {len(created)} observations (ids: {created}).")
        print("Expected: one RED cluster (lighting/safety), one YELLOW cluster (water/plumbing),")
        print("and one isolated GREEN marker with no cluster (cleanliness).")
        print("Start the server and check GET /alerts/ (should show 1 red alert) and")
        print("GET /observations/ (should show all 8 markers) to confirm.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
