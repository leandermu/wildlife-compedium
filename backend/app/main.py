from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import achievements, backup, export, observations, photos, profiles, species, stats
from .seed import ensure_seeded


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_seeded()
    yield


app = FastAPI(
    title="Wildlife Compedium API",
    description="Persönliches Tierfoto-Compedium",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(profiles.router)
app.include_router(species.router)
app.include_router(observations.router)
app.include_router(photos.router)
app.include_router(achievements.router)
app.include_router(backup.router)
app.include_router(export.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# personal photos are served from here; in production put a real web server or
# an object store in front of it (see storage.py)
settings.local_media_path.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.media_base_url,
    StaticFiles(directory=settings.local_media_path),
    name="media",
)
