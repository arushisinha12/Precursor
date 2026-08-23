from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import engine
from models import Base

from routes.observations import router as observations_router
from routes.clusters import router as clusters_router
from routes.alerts import router as alerts_router
from routes.auth import router as auth_router


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Precursor API")

# Kept even though frontend and backend are now served from the same
# origin/port - harmless locally, and means the API can still be hit
# directly (e.g. http://localhost:8000/docs) or from a separate dev
# server without breaking.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(observations_router)
app.include_router(clusters_router)
app.include_router(alerts_router)
app.include_router(auth_router)


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api")
def api_root():
    return {"message": "Precursor backend is running"}


# Single-app setup: the frontend (static/index.html) is served directly by
# this same FastAPI process, so there's only one server to start and one
# port to open. The API stays under /observations, /clusters, /alerts as
# before; everything else falls through to the static frontend.
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


@app.exception_handler(404)
async def spa_fallback(request, exc):
    # Any unmatched path (e.g. a browser refresh on a client route) still
    # gets the frontend shell instead of a bare 404.
    return FileResponse(STATIC_DIR / "index.html")
