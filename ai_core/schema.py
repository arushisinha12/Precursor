# schema.py
# This file defines the fixed contract between AI/ML and Backend.
# Do not invent tags outside this list — keep AI output consistent.

ALLOWED_TAGS = [
    "lighting",
    "electrical",
    "water",
    "plumbing",
    "structural",
    "cleanliness",
    "overflow",
    "accessibility",
    "crowding",
    "equipment",
    "safety",
    "other"
]

SEVERITY_SCALE = {
    1: "very minor",
    2: "minor",
    3: "moderate",
    4: "serious",
    5: "critical / immediate hazard"
}

# Expected output shape sent to backend:
# {
#   "tags": ["lighting", "electrical"],
#   "severity": 3
# }