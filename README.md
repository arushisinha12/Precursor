# Precursor — single-app prototype

Detect problems before they become incidents. This is the whole app —
frontend + backend + AI tagging + clustering/scoring — merged into **one**
FastAPI process, so there's one thing to install and one thing to run.

The backend logic (models, scoring, clustering, AI tagging fallback) is
unchanged from the original prototype. The only thing that changed is how
the frontend is served: instead of a separate Next.js dev server, the same
visual design (dark theme, live map, report form, alert cards) is now a
single static page (`static/index.html`) served directly by FastAPI, so you
don't need Node/npm at all — just Python.

## Run it

```bash
cd precursor
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **http://localhost:8000** in your browser. That's it — the API
and the frontend are the same server on the same port.

## What you can do

- **Report an observation**: click "Report observation", optionally add a
  photo, write what you noticed, allow location access (or it falls back to
  an area-center default), submit.
- The backend immediately runs it through the AI tagging/severity pipeline
  (`ai_core/observation_analyzer.py`) and the response is shown right in the
  form: assigned **tags** and a **severity score (1–5)**.
- It also runs clustering (`services/clustering.py`): if this observation is
  near others sharing a tag (within 100m), they're grouped into a cluster,
  and an **emergence score** is computed (`services/scoring.py`) from report
  count × distinct users × average severity × recency. Clusters scoring
  above the threshold turn into map alerts.
- Click any marker on the map to see its details — severity, average
  severity for its cluster, emergence score, status (green/yellow/red →
  observation/emerging/urgent), tags, and photos.

## AI tagging: works with no API key

By default there's no `GEMINI_API_KEY` set, so tagging/severity uses a
built-in offline keyword-based analyzer (see
`ai_core/observation_analyzer.py`) — the app is fully functional out of the
box with zero configuration.

To use real Gemini-based analysis instead:

```bash
cp .env.example .env
# then edit .env and set GEMINI_API_KEY=your-key-here
# (get a free key at https://aistudio.google.com/app/apikey)
```

## Data storage

Defaults to a local SQLite file (`precursor.db`, created automatically on
first run). To use Postgres instead, set `DATABASE_URL` in `.env` and
`pip install psycopg2-binary`.

## Project structure

```
precursor/
├── main.py                       # FastAPI app: mounts API routes + serves static/index.html
├── database.py                   # SQLAlchemy engine/session (SQLite by default)
├── models.py                     # Observation, Cluster tables
├── schemas.py                    # Pydantic request/response models
├── ai_config.py                  # Gemini key / offline-fallback switch
├── ai_core/
│   ├── schema.py                 # Fixed tag list + severity scale (AI/backend contract)
│   └── observation_analyzer.py   # Gemini analysis + offline keyword fallback
├── services/
│   ├── clustering.py             # Groups nearby same-tag observations into clusters
│   └── scoring.py                # Emergence score + green/yellow/red status
├── routes/
│   ├── observations.py           # POST/GET /observations
│   ├── clusters.py                # GET /clusters
│   └── alerts.py                  # GET /alerts (red clusters, with rolled-up tags/photos)
├── static/
│   └── index.html                # The entire frontend (HTML+CSS+JS), same design as before
└── requirements.txt
```
