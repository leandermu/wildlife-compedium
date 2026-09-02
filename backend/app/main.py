from contextlib import asynccontextmanager
from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import achievements, backup, export, observations, photos, profiles, species, stats
from .seed import ensure_seeded


def ensure_reference_plates() -> None:
    """Populate only missing bundled plates inside the persistent media volume."""
    script = Path(__file__).resolve().parent.parent / "scripts" / "process_reference_images.py"
    originals = Path("/images/original")
    if not originals.exists():
        originals = script.parent.parent.parent / "images" / "original"
    if not script.exists() or not originals.exists() or not any(originals.glob("*.jpg")):
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--missing"],
            check=True,
            timeout=240,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        # Reference plates are decorative; the API must remain available when
        # one corrupt source image cannot be processed.
        print(f"Referenzbilder konnten nicht vollständig verarbeitet werden: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_seeded()
    photos.ensure_browser_derivatives()
    ensure_reference_plates()
    yield


app = FastAPI(
    title="Wildlife Compedium API",
    description="Persönliches Tierfoto-Compedium",
    version="1.0.0",
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
