from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List


class ObservationCreate(BaseModel):
    user_id: str
    description: str
    photo_url: Optional[str] = None
    latitude: float
    longitude: float


class AIResult(BaseModel):
    tags: List[str]
    severity: int


class ObservationResponse(BaseModel):
    id: int
    user_id: str
    description: str
    photo_url: Optional[str]
    latitude: float
    longitude: float
    timestamp: datetime
    tags: Optional[List[str]]
    severity: Optional[int]
    needs_review: bool = False

    class Config:
        from_attributes = True


class ClusterResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    observation_count: int
    distinct_users: int
    average_severity: float
    emergence_score: float
    status: str
    last_seen: datetime

    class Config:
        from_attributes = True