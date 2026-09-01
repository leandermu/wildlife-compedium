from __future__ import annotations

import csv
import io
import json
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Species
from ..profiles import CurrentProfile
from ..queries import SpeciesQuery, display_photos, to_detail, to_list_item
from ..schemas import (
    Facets,
    FacetValue,
    ImportResult,
    Page,
    SpeciesCreate,
    SpeciesDetail,
    SpeciesListItem,
    SpeciesUpdate,
    AutomaticSpeciesCreate,
)
from ..text import slugify
from ..storage import ALLOWED_SUFFIXES, get_storage
from ..vocab import DIFFICULTIES, GROUPS, HABITATS, REGIONS, STATUSES
from ..wikipedia import import_species_automatically, make_reference_plate

router = APIRouter(prefix="/api/species", tags=["species"])

ListFilter = Annotated[list[str] | None, Query()]


@router.get("", response_model=Page[SpeciesListItem])
def list_species(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    q: str | None = None,
    group: ListFilter = None,
    habitat: ListFilter = None,
    region: ListFilter = None,
    family: ListFilter = None,
    tag: ListFilter = None,
    difficulty: Annotated[list[int] | None, Query()] = None,
    status: ListFilter = None,
    seen: ListFilter = None,
    sort: str = "default",
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(60, ge=1, le=500),
) -> Page[SpeciesListItem]:
    sq = SpeciesQuery(profile.id)
    filters = dict(
        q=q, group=group, habitat=habitat, region=region, family=family, tag=tag,
        difficulty=difficulty, status=status, seen=seen,
        include_inactive=include_inactive,
    )

    total = int(
        db.execute(
            sq.apply_filters(sq.base(func.count(func.distinct(Species.id))), **filters)
        ).scalar()
        or 0
    )

    stmt = sq.apply_filters(
        sq.base(Species, sq.photo_count, sq.has_best, sq.obs_count), **filters
    )
    stmt = sq.apply_sort(stmt, sort).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).all()

    photos = display_photos(db, [r[0].id for r in rows], profile.id)
    items = [
        to_list_item(sp, int(pc), int(oc), bool(hb), photos.get(sp.id))
        for sp, pc, hb, oc in rows
    ]
    return Page[SpeciesListItem](
        items=items, total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.get("/facets", response_model=Facets)
def facets(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    q: str | None = None,
    group: ListFilter = None,
    habitat: ListFilter = None,
    region: ListFilter = None,
    family: ListFilter = None,
    tag: ListFilter = None,
    difficulty: Annotated[list[int] | None, Query()] = None,
    status: ListFilter = None,
    seen: ListFilter = None,
) -> Facets:
    """Counts for every filter dimension, each computed *without* the filter it
    describes, so the sidebar never shows a dead end."""
    sq = SpeciesQuery(profile.id)
    active = dict(q=q, group=group, habitat=habitat, region=region, family=family,
                  tag=tag, difficulty=difficulty, status=status, seen=seen)

    def rows_for(exclude: str):
        f = {k: (None if k == exclude else v) for k, v in active.items()}
        stmt = sq.apply_filters(
            sq.base(Species.id, Species.group, Species.family, Species.difficulty,
                    Species.habitats, Species.regions, Species.tags, sq.photo_count,
                    sq.has_best, sq.obs_count),
            **f,
        )
        return db.execute(stmt).all()

    def scalar_facet(exclude: str, index: int, vocab: dict, key_cast=str) -> list[FacetValue]:
        counts: dict = {}
        for row in rows_for(exclude):
            key = key_cast(row[index])
            total, coll = counts.get(key, (0, 0))
            counts[key] = (total + 1, coll + (1 if row[7] > 0 else 0))
        out = []
        for key, (total, coll) in counts.items():
            meta = vocab.get(key, {}) if vocab else {}
            out.append(FacetValue(
                value=str(key), label=meta.get("label", str(key)), count=total, collected=coll))
        order = {str(k): v.get("order", 99) for k, v in (vocab or {}).items()}
        out.sort(key=lambda f: (order.get(f.value, 99), f.label))
        return out

    def list_facet(exclude: str, index: int, vocab: dict) -> list[FacetValue]:
        counts: dict = {}
        for row in rows_for(exclude):
            for key in row[index] or []:
                total, coll = counts.get(key, (0, 0))
                counts[key] = (total + 1, coll + (1 if row[7] > 0 else 0))
        out = [
            FacetValue(value=k, label=(vocab.get(k, {}) or {}).get("label", k),
                       count=t, collected=c)
            for k, (t, c) in counts.items()
        ]
        order = {k: v.get("order", 99) for k, v in (vocab or {}).items()}
        out.sort(key=lambda f: (order.get(f.value, 99), f.label))
        return out

    status_rows = rows_for("status")
    status_counts = {"locked": 0, "unlocked": 0, "mastered": 0}
    for row in status_rows:
        pc, hb = int(row[7]), int(row[8])
        if pc == 0:
            status_counts["locked"] += 1
        else:
            status_counts["unlocked"] += 1
            if pc >= 2 and hb:
                status_counts["mastered"] += 1

    seen_rows = rows_for("seen")
    seen_counts = {"seen": 0, "unseen": 0}
    for row in seen_rows:
        has_encounter = int(row[7]) > 0 or int(row[9]) > 0
        seen_counts["seen" if has_encounter else "unseen"] += 1

    return Facets(
        groups=scalar_facet("group", 1, GROUPS),
        families=sorted(scalar_facet("family", 2, {}), key=lambda f: -f.count),
        difficulties=scalar_facet("difficulty", 3, {str(k): v for k, v in DIFFICULTIES.items()}),
        habitats=list_facet("habitat", 4, HABITATS),
        regions=list_facet("region", 5, REGIONS),
        tags=sorted(list_facet("tag", 6, {}), key=lambda f: -f.count)[:40],
        statuses=[
            FacetValue(value=k, label=STATUSES[k]["label"], count=v, collected=v)
            for k, v in status_counts.items()
        ],
        seen=[
            FacetValue(
                value=key,
                label="Gesehen" if key == "seen" else "Noch nicht gesehen",
                count=count,
                collected=seen_counts["seen"] if key == "seen" else 0,
            )
            for key, count in seen_counts.items()
        ],
    )


def _get_species(db: Session, key: str) -> Species:
    stmt = select(Species).where(
        Species.id == int(key) if key.isdigit() else Species.slug == key
    )
    sp = db.execute(stmt).scalar_one_or_none()
    if sp is None:
        raise HTTPException(404, "Art nicht gefunden")
    return sp


@router.get("/{key}", response_model=SpeciesDetail)
def get_species(
    key: str, db: Annotated[Session, Depends(get_db)], profile: CurrentProfile
) -> SpeciesDetail:
    return to_detail(_get_species(db, key), profile.id)


@router.post("/automatic", response_model=SpeciesDetail, status_code=201)
@router.post(
    "/from-wikipedia",
    response_model=SpeciesDetail,
    status_code=201,
    include_in_schema=False,
)
def create_species_automatically(
    payload: AutomaticSpeciesCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
):
    """Create a species from validated animal and taxonomy data sources."""
    try:
        imported = import_species_automatically(payload.common_name)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "Die Artendatenquellen konnten nicht erreicht werden.") from exc
    slug = slugify(imported.common_name)
    if db.execute(select(Species).where(Species.slug == slug)).scalar_one_or_none():
        raise HTTPException(409, f"„{imported.common_name}“ ist bereits vorhanden")
    sp = Species(**imported.__dict__, slug=slug)
    sp.refresh_derived()
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return to_detail(sp, profile.id)


@router.post("", response_model=SpeciesDetail, status_code=201)
def create_species(
    payload: SpeciesCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
):
    slug = payload.slug or slugify(payload.common_name)
    if db.execute(select(Species).where(Species.slug == slug)).scalar_one_or_none():
        raise HTTPException(409, f"Slug '{slug}' existiert bereits")
    sp = Species(**payload.model_dump(exclude={"slug"}), slug=slug)
    sp.refresh_derived()
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return to_detail(sp, profile.id)


@router.post("/manual", response_model=SpeciesDetail, status_code=201)
async def create_species_manual(
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
    data: Annotated[str, Form()],
    image: Annotated[UploadFile | None, File()] = None,
) -> SpeciesDetail:
    """Create explicit species fields and optionally process a reference image."""
    try:
        payload = SpeciesCreate.model_validate_json(data)
    except Exception as exc:
        raise HTTPException(422, "Die eingegebenen Artdaten sind ungültig") from exc
    slug = payload.slug or slugify(payload.common_name)
    if db.execute(select(Species).where(Species.slug == slug)).scalar_one_or_none():
        raise HTTPException(409, f"„{payload.common_name}“ ist bereits vorhanden")

    values = payload.model_dump(exclude={"slug"})
    values.update(
        reference_image=None,
        reference_thumb=None,
        reference_credit=None,
        reference_source=None,
    )
    if image is not None:
        raw = await image.read()
        if not raw:
            raise HTTPException(400, "Das Referenzbild ist leer")
        if len(raw) > 40 * 1024 * 1024:
            raise HTTPException(413, "Referenzbild größer als 40 MB")
        suffix = "." + (image.filename or "referenz.jpg").rsplit(".", 1)[-1].lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(415, f"Dateityp {suffix} wird nicht unterstützt")
        try:
            plate = make_reference_plate(raw, 1000)
            thumb = make_reference_plate(raw, 480)
        except Exception as exc:
            raise HTTPException(415, "Das Referenzbild konnte nicht gelesen werden") from exc
        storage = get_storage()
        values["reference_image"] = storage.save(
            "reference", f"{slug}.jpg", io.BytesIO(plate)
        )
        values["reference_thumb"] = storage.save(
            "reference-thumb", f"{slug}.jpg", io.BytesIO(thumb)
        )
        values["reference_credit"] = "Eigenes Referenzbild"

    sp = Species(**values, slug=slug)
    sp.refresh_derived()
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return to_detail(sp, profile.id)


@router.patch("/{key}", response_model=SpeciesDetail)
def update_species(
    key: str,
    payload: SpeciesUpdate,
    db: Annotated[Session, Depends(get_db)],
    profile: CurrentProfile,
):
    sp = _get_species(db, key)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sp, field, value)
    sp.refresh_derived()
    db.commit()
    db.refresh(sp)
    return to_detail(sp, profile.id)


@router.delete("/{key}", status_code=204)
def delete_species(key: str, db: Annotated[Session, Depends(get_db)]) -> None:
    sp = _get_species(db, key)
    db.delete(sp)
    db.commit()


# ------------------------------------------------------------------ import --
LIST_FIELDS = {"habitats", "regions", "countries", "tags"}
ALLOWED = set(SpeciesCreate.model_fields) | {"slug"}


def _coerce(row: dict) -> dict:
    out: dict = {}
    for key, value in row.items():
        key = (key or "").strip()
        if key not in ALLOWED or value is None:
            continue
        if key in LIST_FIELDS and isinstance(value, str):
            out[key] = [v.strip() for v in value.replace(";", ",").split(",") if v.strip()]
        elif key == "difficulty":
            try:
                out[key] = max(1, min(5, int(str(value).strip() or 1)))
            except ValueError:
                out[key] = 1
        elif key == "active" and isinstance(value, str):
            out[key] = value.strip().lower() not in {"0", "false", "nein", "no", ""}
        else:
            out[key] = value
    return out


def upsert_rows(db: Session, rows: list[dict], update_existing: bool = True) -> ImportResult:
    created = updated = skipped = 0
    errors: list[str] = []
    for i, raw in enumerate(rows, start=1):
        try:
            data = _coerce(raw)
            if not data.get("common_name"):
                errors.append(f"Zeile {i}: 'common_name' fehlt")
                skipped += 1
                continue
            slug = data.pop("slug", None) or slugify(data["common_name"])
            sp = db.execute(select(Species).where(Species.slug == slug)).scalar_one_or_none()
            if sp is None:
                sp = Species(slug=slug, **{k: v for k, v in data.items()})
                sp.refresh_derived()
                db.add(sp)
                created += 1
            elif update_existing:
                for k, v in data.items():
                    setattr(sp, k, v)
                sp.refresh_derived()
                updated += 1
            else:
                skipped += 1
        except Exception as exc:  # keep importing the remaining rows
            errors.append(f"Zeile {i}: {exc}")
            skipped += 1
    db.commit()
    return ImportResult(created=created, updated=updated, skipped=skipped, errors=errors[:50])


@router.post("/import", response_model=ImportResult)
def import_species(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[list[dict] | None, Body()] = None,
    update_existing: bool = True,
) -> ImportResult:
    if not payload:
        raise HTTPException(400, "Leere Nutzlast")
    return upsert_rows(db, payload, update_existing)


@router.post("/import/file", response_model=ImportResult)
async def import_species_file(
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile,
    update_existing: bool = True,
) -> ImportResult:
    raw = (await file.read()).decode("utf-8-sig")
    name = (file.filename or "").lower()
    if name.endswith(".json") or raw.lstrip().startswith(("[", "{")):
        data = json.loads(raw)
        rows = data if isinstance(data, list) else data.get("species", [])
    else:
        dialect = csv.Sniffer().sniff(raw[:2048], delimiters=",;\t") if raw.strip() else csv.excel
        rows = list(csv.DictReader(io.StringIO(raw), dialect=dialect))
    if not isinstance(rows, list):
        raise HTTPException(400, "Format nicht erkannt")
    return upsert_rows(db, rows, update_existing)
