from math import radians, sin, cos, sqrt, atan2

from models import Observation, Cluster
from services.scoring import (
    calculate_emergence_score,
    get_status
)


MAX_DISTANCE_METERS = 100


def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def have_common_tag(tags1, tags2):
    if not tags1 or not tags2:
        return False

    return bool(set(tags1) & set(tags2))


def find_matching_observations(new_observation, observations):
    matches = []

    for observation in observations:

        if observation.id == new_observation.id:
            continue

        if not have_common_tag(
            new_observation.tags,
            observation.tags
        ):
            continue

        distance = calculate_distance(
            new_observation.latitude,
            new_observation.longitude,
            observation.latitude,
            observation.longitude
        )

        if distance <= MAX_DISTANCE_METERS:
            matches.append(observation)

    return matches


def update_cluster(new_observation, db):

    if not new_observation.tags or not new_observation.severity:
        return None

    all_observations = db.query(Observation).filter(
        Observation.tags.isnot(None),
        Observation.severity.isnot(None)
    ).all()

    matches = find_matching_observations(
        new_observation,
        all_observations
    )

    cluster_observations = matches + [new_observation]

    if len(cluster_observations) < 2:
        return None

    latitude = sum(
        observation.latitude
        for observation in cluster_observations
    ) / len(cluster_observations)

    longitude = sum(
        observation.longitude
        for observation in cluster_observations
    ) / len(cluster_observations)

    users = {
        observation.user_id
        for observation in cluster_observations
    }

    average_severity = sum(
        observation.severity
        for observation in cluster_observations
    ) / len(cluster_observations)

    last_seen = max(
        observation.timestamp
        for observation in cluster_observations
    )

    existing_cluster = None

    clusters = db.query(Cluster).all()

    for cluster in clusters:

        distance = calculate_distance(
            latitude,
            longitude,
            cluster.latitude,
            cluster.longitude
        )

        if distance <= MAX_DISTANCE_METERS:
            existing_cluster = cluster
            break

    if existing_cluster:

        existing_cluster.latitude = latitude
        existing_cluster.longitude = longitude
        existing_cluster.observation_count = len(
            cluster_observations
        )
        existing_cluster.distinct_users = len(users)
        existing_cluster.average_severity = average_severity
        existing_cluster.last_seen = last_seen

        score = calculate_emergence_score(
            existing_cluster.observation_count,
            existing_cluster.distinct_users,
            existing_cluster.average_severity,
            existing_cluster.last_seen
        )

        existing_cluster.emergence_score = score
        existing_cluster.status = get_status(score)

        for observation in cluster_observations:
            observation.cluster_id = existing_cluster.id

        db.commit()
        db.refresh(existing_cluster)

        return existing_cluster

    score = calculate_emergence_score(
        len(cluster_observations),
        len(users),
        average_severity,
        last_seen
    )

    new_cluster = Cluster(
        latitude=latitude,
        longitude=longitude,
        observation_count=len(cluster_observations),
        distinct_users=len(users),
        average_severity=average_severity,
        last_seen=last_seen,
        emergence_score=score,
        status=get_status(score)
    )

    db.add(new_cluster)
    db.commit()
    db.refresh(new_cluster)

    for observation in cluster_observations:
        observation.cluster_id = new_cluster.id
    db.commit()

    return new_cluster