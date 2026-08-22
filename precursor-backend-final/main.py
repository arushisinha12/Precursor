from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from models import Base

from routes.observations import router as observations_router
from routes.clusters import router as clusters_router
from routes.alerts import router as alerts_router


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Precursor API")

# Frontend runs on a different origin/port (e.g. http://localhost:3000)
# than this backend (e.g. http://localhost:8000). Without this, the
# browser blocks every fetch() call from frontend even though both
# servers are running fine — this is not optional for local dev either.
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


@app.get("/")
def root():
    return {"message": "Precursor backend is running"}