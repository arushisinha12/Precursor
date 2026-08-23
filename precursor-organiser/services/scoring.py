from datetime import datetime, timezone


def calculate_recency_factor(last_seen):
    now = datetime.now(timezone.utc)

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    hours_since_last_observation = (
        now - last_seen
    ).total_seconds() / 3600

    if hours_since_last_observation <= 1:
        return 1.0

    if hours_since_last_observation <= 6:
        return 0.8

    if hours_since_last_observation <= 12:
        return 0.6

    if hours_since_last_observation <= 24:
        return 0.4

    return 0.1


def calculate_emergence_score(
    observation_count,
    distinct_users,
    average_severity,
    last_seen
):
    recency = calculate_recency_factor(last_seen)

    score = (
        observation_count
        * distinct_users
        * average_severity
        * recency
    )

    return round(score, 2)


def get_status(score):

    if score < 20:
        return "green"

    if score <= 50:
        return "yellow"

    return "red"