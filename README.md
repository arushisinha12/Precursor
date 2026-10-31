# Precursor

Precursor is a prototype for detecting issues before they become incidents. It combines a map-based reporting interface, AI-assisted issue classification, clustering of nearby reports, and a simple operational dashboard for review and resolution.

The app was designed as a single-service prototype: the FastAPI backend, the API routes, and the frontend are all served from one Python process. That means there is only one server to run and one port to open.

## Why this exists

The project models a simple real-world workflow:

- a person notices a problem in a physical location
- they report it with a location and optionally a photo
- the app classifies the issue with tags like lighting, water, safety, accessibility, etc.
- related reports are grouped into clusters when they are near each other and share a concern
- the system estimates whether the pattern is emerging or urgent
- an organiser can review individual reports and cluster-level alerts

This is useful for campus operations, facilities management, public infrastructure tracking, or any environment where “signals” surface in a physical space and need triage.

## Features

- Map-based reporting dashboard
- Browser geolocation support with area-center fallback
- Optional photo upload for evidence
- AI tag and severity inference using Gemini when configured
- Offline fallback analysis when no API key is configured
- Nearby report clustering within a 100m radius
- Emergence scoring and color-coded status thresholds
- Alerts for urgent red clusters
- Organiser dashboard for unresolved observations and clusters
- Basic signup/login flow for users
- Local SQLite-backed prototype database by default

## Tech stack

- Python 3
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite by default; PostgreSQL supported via DATABASE_URL
- Leaflet for map visuals in the frontend
- Google Gemini for optional live AI classification
- bcrypt + itsdangerous for lightweight auth demo

## Quick start

### 1) Create and activate a virtual environment

```bash
cd /path/to/Precursor
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Start the app

```bash
uvicorn main:app --reload
```

Then open:

```text
http://localhost:8000
```

The API documentation is also available at:

```text
http://localhost:8000/docs
```

## Configuration

### Use the app without any API key

By default, the app runs in offline mode. No `GEMINI_API_KEY` is required, and the project still works using a built-in keyword analyzer.

### Use Gemini for live AI analysis

Copy the example environment file and add your key:

```bash
cp .env.example .env
```

Then edit `.env` and set:

```bash
GEMINI_API_KEY=your_key_here
```

The AI pipeline uses a fixed tag and severity contract defined in `ai_core/schema.py`.

## Data storage

The app defaults to a local SQLite database file:

```text
precursor.db
```

This file is created automatically on first run.

If you want to use Postgres instead, set `DATABASE_URL` in `.env` and install the driver:

```bash
pip install psycopg2-binary
```

## Application flow

A typical report follows this path:

1. User opens the frontend and clicks “Report observation”
2. They add an optional photo, description, and location
3. The browser submits the report to `POST /observations/`
4. The backend creates an `Observation` record
5. AI analysis runs:
   - Gemini if configured
   - keyword fallback if not
6. Tags and severity are assigned and stored
7. Cluster logic groups nearby reports that share tags within 100m
8. Emergence score and red/yellow/green status are calculated
9. The frontend re-renders markers and alert widgets

## Project structure

```text
Precursor/
├── main.py                          # FastAPI app entry point; serves backend + frontend
├── database.py                      # SQLAlchemy engine, DB session, SQLite migration helper
├── models.py                        # SQLAlchemy models: Observation, User, Cluster
├── schemas.py                       # Pydantic request/response models
├── ai_config.py                     # Gemini toggle and model config
├── ai_core/
│   ├── __init__.py
│   ├── schema.py                    # Allowed AI tags and severity mapping
│   └── observation_analyzer.py      # Gemini + offline keyword fallback analysis
├── services/
│   ├── __init__.py
│   ├── clustering.py                # Nearby same-tag clustering logic
│   └── scoring.py                   # Emergence score + status calculation
├── routes/
│   ├── __init__.py
│   ├── observations.py              # Observation create/read/resolve APIs
│   ├── clusters.py                  # Cluster read/resolve APIs
│   ├── alerts.py                    # Red-cluster alert aggregation
│   └── auth.py                      # Signup/login API
├── static/
│   └── index.html                   # Frontend UI: map, forms, auth, organiser views
├── test_data/
│   ├── README.md
│   ├── seed_demo_data.py            # Seeds clustered demo data without AI
│   ├── seed_observations.py         # Posts synthetic observations to real API
│   ├── generate_synthetic_data.py   # Generates synthetic issue data
│   └── sample_categories.py         # Category helpers for synthetic seeds
├── .env.example                     # Example environment config
├── requirements.txt                 # Python dependencies
├── README.md                       # Project documentation
└── precursor.db                    # Generated local SQLite DB at runtime
```

## API overview

### Observations

- `POST /observations/` - create a new observation
- `GET /observations/` - return all observation records
- `GET /observations/organiser` - organiser queue, unresolved first
- `PATCH /observations/{id}/resolve` - mark one report addressed
- `PATCH /observations/{id}/ai` - override AI tags/severity manually

### Clusters

- `GET /clusters/` - return cluster list
- `GET /clusters/organiser` - priority-ordered cluster list for organisers
- `PATCH /clusters/{id}/resolve` - mark a cluster resolved

### Alerts

- `GET /alerts/` - return clusters in red status with aggregated tags and photos

### Auth

- `POST /auth/signup` - create an account
- `POST /auth/login` - log in and receive a signed token

## AI tagging model

The app uses a fixed set of allowed tags:

- lighting
- electrical
- water
- plumbing
- structural
- cleanliness
- overflow
- accessibility
- crowding
- equipment
- safety
- other

Severity is mapped to a 1–5 scale, where higher numbers represent more urgent conditions.

If no Gemini key is configured, a lightweight offline keyword matcher still assigns tags and severity, allowing the app to remain fully usable in demos and local development.

## Clustering and scoring logic

Observations are clustered when:

- they are within 100m of each other
- they share at least one tag

The cluster score is calculated from:

- number of reports
- number of distinct users
- average severity
- recency of the latest report

Status thresholds:

- green: <20
- yellow: 20–50
- red: >50

This makes the project usable as a prototype for identifying recurring patterns before they become major incidents.

## Demo / test data

A demo data workflow exists under `test_data/`.

### Seed fixed sample data

```bash
python -m test_data.seed_demo_data
```

This creates a quick demo with:

- one red cluster
- one yellow cluster
- one isolated green report

No AI dependency is required.

### Seed the real API pipeline

Start the backend first, then run:

```bash
cd test_data
python generate_synthetic_data.py
python seed_observations.py --url http://localhost:8000
```

This uses the actual `/observations/` endpoint and exercises the live tagging and clustering behavior.

## Notes on implementation

### Single-app architecture

The project intentionally serves both the API and frontend from one FastAPI app. This reduces friction in local development and demos, and keeps deployment simple.

### Offline-first design

The app is purposely built to work without external dependencies or an API key. That makes it easy to run anywhere and convenient for presentations, prototypes, and local validation.

### Minimal but functional auth

The auth system is intentionally lightweight rather than enterprise-grade. It is good for a prototype, but not a production identity model.

## Troubleshooting

### The app starts but the map is empty

Make sure the backend is running and that the SQLite database exists. If needed, seed demo data:

```bash
python -m test_data.seed_demo_data
```

### AI analysis is not running

This normally means `GEMINI_API_KEY` is not configured. The app will automatically fall back to offline detection.

### The frontend cannot reach the API

Check that the app is running at `http://localhost:8000` and that there are no port conflicts.

## License

This project is a prototype and is intended for demo, exploration, and internal evaluation use.

## Summary

Precursor is a compact problem-detection prototype for physical-space monitoring. It turns local reports into clustered insights, uses AI or fallback heuristics to classify issues, and helps surface emerging hotspots before they become serious incidents.
