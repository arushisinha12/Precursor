from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Cluster, Observation
from schemas import ClusterResponse


router = APIRouter(
    prefix="/clusters",
    tags=["Clusters"]
)


@router.get("/", response_model=list[ClusterResponse])
def get_clusters(db: Session = Depends(get_db)):
    return db.query(Cluster).all()


@router.get("/organiser")
def get_organiser_clusters(db: Session = Depends(get_db)):
    """Every cluster (any status), unresolved first, priority-sorted by
    emergence_score - for the Organiser priority list."""
    clusters = db.query(Cluster).order_by(Cluster.resolved.asc(), Cluster.emergence_score.desc()).all()
    result = []
    for c in clusters:
        tags = []
        for obs in db.query(Observation).filter(Observation.cluster_id == c.id).all():
            for t in (obs.tags or []):
                if t not in tags:
                    tags.append(t)
        result.append({
            "id": c.id, "latitude": c.latitude, "longitude": c.longitude,
            "observation_count": c.observation_count, "distinct_users": c.distinct_users,
            "average_severity": c.average_severity, "emergence_score": c.emergence_score,
            "status": c.status, "resolved": c.resolved, "last_seen": c.last_seen, "tags": tags,
        })
    return result


@router.patch("/{cluster_id}/resolve")
def resolve_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    cluster.resolved = True
    db.commit()
    return {"id": cluster.id, "resolved": True}