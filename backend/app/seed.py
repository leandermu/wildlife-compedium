"""Seeds the species catalogue from app/data/seed_species.json.

Idempotent: existing species (matched by slug) are updated, personal data
(photos, observations) is never touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import func, select

from .db import SessionLocal, init_db
from .models import Species
from .text import slugify

SEED_FILE = Path(__file__).parent / "data" / "seed_species.json"


def load_seed_rows() -> list[dict]:
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


def seed(force: bool = False, quiet: bool = False) -> tuple[int, int]:
    init_db()
    rows = load_seed_rows()
    created = updated = 0
    with SessionLocal() as db:
        existing = {s.slug: s for s in db.execute(select(Species)).scalars()}
        for index, row in enumerate(rows):
            slug = row.get("slug") or slugify(row["common_name"])
            sp = existing.get(slug)
            if sp is None:
                sp = Species(slug=slug, sort_index=index, **row)
                sp.refresh_derived()
                db.add(sp)
                created += 1
            elif force:
                for key, value in row.items():
                    setattr(sp, key, value)
                sp.sort_index = index
                sp.refresh_derived()
                updated += 1
        db.commit()
        total = int(db.execute(select(func.count(Species.id))).scalar() or 0)
    if not quiet:
        print(f"Seed: {created} neu, {updated} aktualisiert, {total} Arten gesamt.")
    return created, updated


def ensure_seeded() -> None:
    """Called on startup — fills an empty database so the app is never blank."""
    init_db()
    with SessionLocal() as db:
        if int(db.execute(select(func.count(Species.id))).scalar() or 0) == 0:
            seed(quiet=True)


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
