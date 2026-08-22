import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from google.api_core.exceptions import ResourceExhausted

from database import get_db
from models import Observation
from schemas import (
    ObservationCreate,
    ObservationResponse,
    AIResult
)
from services.clustering import update_cluster
from ai_core.observation_analyzer import analyze_observation


def analyze_with_retry(description, photo_url=None, max_retries=2, wait_seconds=15):
    """
    Same rate-limit handling as AI/ML's main.py (catches ResourceExhausted
    and waits), but capped so a live request can't hang indefinitely if
    the free-tier quota is hit during a demo.

    If retries are exhausted, or any other AI/network error occurs, falls
    back to {"tags": ["other"], "severity": 3, "needs_review": True} — a
    moderate severity, not the lowest tier. This is deliberate: a technical
    failure (bad network, rate limit) tells us nothing about how serious
    the actual observation is, so defaulting low risks silently burying a
    real hazard just because the AI call happened to fail. Defaulting to
    moderate errs toward "flag it for a human to check" rather than
    "assume it's nothing." needs_review lets the UI surface that this
    severity was estimated, not AI-confirmed, so a human can double-check.
    """
    attempt = 0
    while True:
        try:
            result = analyze_observation(description=description, photo_url=photo_url)
            result["needs_review"] = False
            return result
        except ResourceExhausted:
            attempt += 1
            if attempt > max_retries:
                print(f"Rate limit still exceeded after {max_retries} retries, using moderate fallback severity.")
                return {"tags": ["other"], "severity": 3, "needs_review": True}
            print(f"Rate limit hit, waiting {wait_seconds}s (attempt {attempt}/{max_retries})...")
            time.sleep(wait_seconds)
        except Exception as e:
            print(f"AI analysis error ({e}), using moderate fallback severity.")
            return {"tags": ["other"], "severity": 3, "needs_review": True}


router = APIRouter(
    prefix="/observations",
    tags=["Observations"]
)


@router.post("/", response_model=ObservationResponse)
def create_observation(
    observation: ObservationCreate,
    db: Session = Depends(get_db)
):
    new_observation = Observation(
        user_id=observation.user_id,
        description=observation.description,
        photo_url=observation.photo_url,
        latitude=observation.latitude,
        longitude=observation.longitude
    )

    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)

    try:
        ai_result = analyze_with_retry(
            description=new_observation.description,
            photo_url=new_observation.photo_url
        )
        new_observation.tags = ai_result["tags"]
        new_observation.severity = ai_result["severity"]
        new_observation.needs_review = ai_result.get("needs_review", False)
        db.commit()
        db.refresh(new_observation)

        update_cluster(new_observation, db)
    except Exception as e:
        print(f"AI analysis failed for observation {new_observation.id}: {e}")

    return new_observation


@router.get("/", response_model=list[ObservationResponse])
def get_observations(db: Session = Depends(get_db)):
    return db.query(Observation).all()


@router.patch("/{observation_id}/ai", response_model=ObservationResponse)
def update_ai_result(
    observation_id: int,
    ai_result: AIResult,
    db: Session = Depends(get_db)
):
    observation = db.query(Observation).filter(
        Observation.id == observation_id
    ).first()

    if observation is None:
        return {"error": "Observation not found"}

    observation.tags = ai_result.tags
    observation.severity = ai_result.severity

    db.commit()
    db.refresh(observation)

    update_cluster(observation, db)

    return observation