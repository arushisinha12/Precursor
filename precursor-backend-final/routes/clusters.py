from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Cluster
from schemas import ClusterResponse


router = APIRouter(
    prefix="/clusters",
    tags=["Clusters"]
)


@router.get("/", response_model=list[ClusterResponse])
def get_clusters(db: Session = Depends(get_db)):
    return db.query(Cluster).all()