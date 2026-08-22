from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Cluster, Observation


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/")
def get_alerts(db: Session = Depends(get_db)):

    clusters = db.query(Cluster).filter(
        Cluster.status == "red"
    ).all()

    alerts = []

    for cluster in clusters:

        contributing_observations = db.query(Observation).filter(
            Observation.cluster_id == cluster.id
        ).all()

        # Roll up all unique tags across contributing observations, so an
        # alert can show e.g. ["lighting", "electrical"] instead of nothing —
        # picks up mixed issue types within the same cluster rather than
        # collapsing to a single "most common" tag.
        all_tags = []
        for observation in contributing_observations:
            if observation.tags:
                for tag in observation.tags:
                    if tag not in all_tags:
                        all_tags.append(tag)

        photos = [
            observation.photo_url
            for observation in contributing_observations
            if observation.photo_url
        ]

        alerts.append({
            "cluster_id": cluster.id,
            "latitude": cluster.latitude,
            "longitude": cluster.longitude,
            "observation_count": cluster.observation_count,
            "distinct_users": cluster.distinct_users,
            "average_severity": cluster.average_severity,
            "emergence_score": cluster.emergence_score,
            "status": cluster.status,
            "last_seen": cluster.last_seen,
            "tags": all_tags,
            "photos": photos
        })

    return alerts