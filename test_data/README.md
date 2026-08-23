# Demo data — two options

## 1. seed_demo_data.py — fast, guaranteed, offline
Writes observations straight to the database and sets tags/severity itself
(no AI call), then runs the real clustering logic. Produces exactly:
- 1 RED cluster (lighting/safety, score 60)
- 1 YELLOW cluster (water/plumbing, score 24)
- 1 isolated GREEN marker with no cluster (only 1 report)

No server needs to be running. No GEMINI_API_KEY needed. Use this as your
safety net right before presenting, or any time you just need clusters on
the map fast.

    python -m test_data.seed_demo_data

## 2. generate_synthetic_data.py + seed_observations.py — realistic, full pipeline
Generates a larger, more realistic dataset (30 background reports + 1
intentional 5-report cluster) across all 12 issue categories, then POSTs
each one to the real running `/observations/` endpoint — so it exercises
the actual AI tagging (or offline fallback) and clustering exactly as a
real user submission would.

Needs the backend running first. Takes a few minutes (intentionally
throttled so it doesn't trip Gemini's rate limit).

    cd test_data
    python generate_synthetic_data.py          # writes synthetic_observations.json
    python seed_observations.py --url http://localhost:8000

Use this earlier, during testing, to prove the full pipeline actually
works — not seconds before you go on stage.
