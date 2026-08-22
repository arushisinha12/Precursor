from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, nullable=False)

    description = Column(String, nullable=False)

    photo_url = Column(String, nullable=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    tags = Column(JSON, nullable=True)

    severity = Column(Integer, nullable=True)

    needs_review = Column(Boolean, default=False)

    # Links this observation to the cluster it contributed to (set in
    # services/clustering.py). Lets alerts pull real tags/photos from their
    # contributing observations instead of showing generic placeholders.
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    observation_count = Column(Integer, default=0)
    distinct_users = Column(Integer, default=0)

    average_severity = Column(Float, default=0)

    emergence_score = Column(Float, default=0)

    status = Column(String, default="green")

    last_seen = Column(DateTime(timezone=True))