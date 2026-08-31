# syntax=docker/dockerfile:1

# Referenzbilder einmal beim Bauen holen statt bei jedem Start.
#
# Die Skripte leiten ihre Pfade aus der Repo-Struktur ab (<root>/images neben
# <root>/backend); im Image liegt das Backend unter /app, also ist /images genau
# der Ort, an dem sie ohnehin suchen. Der Cache-Mount sorgt dafür, dass ein
# zweiter Build Wikipedia nicht erneut belästigt; weil Cache-Mounts nicht in die
# Schicht wandern, wird das Ergebnis im selben Schritt nach /out kopiert.
FROM python:3.14-slim AS reference

ARG REFERENCE_IMAGES=1

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip pip install pillow

COPY app ./app
COPY scripts ./scripts

RUN --mount=type=cache,target=/images,sharing=locked \
    set -eu; \
    mkdir -p /out; \
    if [ "$REFERENCE_IMAGES" = "1" ]; then \
        python scripts/fetch_reference_images.py; \
        cp -a /images/. /out/; \
    else \
        echo "REFERENCE_IMAGES=0 – Referenzbilder werden nicht geladen"; \
    fi


FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first, from pyproject alone: this layer survives normal code
# edits. The package stub is only there so the build backend has something to
# build; the real install follows below.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install ".[postgres]"

COPY app ./app
COPY scripts ./scripts
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps -e .

# Personal photos live here; compose mounts a volume on it so they survive a
# rebuild. The database is a separate service (see compose.yml).
RUN mkdir -p /app/data/media \
    && useradd --create-home --uid 10001 wildlife \
    && chown -R wildlife:wildlife /app
USER wildlife

# Wikipedia-Vorlagen samt Urheber- und Lizenzangaben (images/credits.json).
COPY --from=reference --chown=10001:10001 /out /images

ENV WC_STORAGE_LOCAL_DIR=/app/data/media

EXPOSE 8000

# The 152 species are seeded on startup by app/seed.py:ensure_seeded().
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
