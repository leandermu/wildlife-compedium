from collections.abc import Iterator

from sqlalchemy import create_engine, event, inspect, select, text, update
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, future=True, **_engine_kwargs())

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - trivial
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_columns() -> None:
    """Ergänzt neu hinzugekommene Spalten in bestehenden Tabellen.

    Bewusst klein gehalten: nur additiv, nie löschend. Für alles Weitergehende
    (Umbenennungen, Typwechsel) gehört später ein echtes Migrationswerkzeug her.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            have = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in have or not column.nullable:
                    continue
                type_sql = column.type.compile(engine.dialect)
                conn.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {type_sql}')
                )


def _ensure_default_profile() -> None:
    """Create the first profile and attach data made before profiles existed."""
    from .models import (
        AchievementState,
        Observation,
        Profile,
        ProfileAchievementState,
        UserPhoto,
    )

    with SessionLocal.begin() as db:
        profile = db.execute(
            select(Profile).order_by(Profile.is_default.desc(), Profile.id)
        ).scalars().first()
        if profile is None:
            profile = Profile(name="Leander", is_default=True)
            db.add(profile)
            db.flush()
        elif not profile.is_default:
            profile.is_default = True
        db.execute(
            update(Observation)
            .where(Observation.profile_id.is_(None))
            .values(profile_id=profile.id)
        )
        db.execute(
            update(UserPhoto)
            .where(UserPhoto.profile_id.is_(None))
            .values(profile_id=profile.id)
        )
        migrated_ids = set(db.execute(
            select(ProfileAchievementState.achievement_id).where(
                ProfileAchievementState.profile_id == profile.id
            )
        ).scalars())
        for old_state in db.execute(select(AchievementState)).scalars():
            if old_state.achievement_id not in migrated_ids:
                db.add(ProfileAchievementState(
                    profile_id=profile.id,
                    achievement_id=old_state.achievement_id,
                    tier=old_state.tier,
                    unlocked_at=old_state.unlocked_at,
                ))


def _ensure_shared_profile() -> None:
    """Create the protected aggregate profile once for existing installations."""
    from .models import Profile

    with SessionLocal.begin() as db:
        shared = db.execute(
            select(Profile).where(Profile.is_shared.is_(True))
        ).scalars().first()
        if shared is None:
            shared = db.execute(
                select(Profile).where(Profile.name.ilike("Gemeinsam"))
            ).scalars().first()
        if shared is None:
            shared = Profile(
                name="Gemeinsam", avatar="👥", gender="male",
                is_shared=True, is_default=False,
            )
            db.add(shared)
        else:
            shared.is_shared = True
            shared.avatar = "👥"
            shared.is_default = False


def _ensure_linked_encounters() -> None:
    """Unify photo/observation fields from versions that stored them separately."""
    from .encounters import reconcile_linked_encounters

    with SessionLocal.begin() as db:
        from .models import Observation, Profile, UserPhoto

        for profile in db.execute(select(Profile)).scalars():
            if profile.exclude_captive_from_progress is None:
                profile.exclude_captive_from_progress = False
        for photo in db.execute(select(UserPhoto)).scalars():
            if not photo.encounter_type:
                value = (photo.photo_metadata or {}).get("encounter_type", "wild")
                photo.encounter_type = value if value in {"wild", "captive"} else "wild"
        for observation in db.execute(select(Observation)).scalars():
            if not observation.encounter_type:
                linked = next(iter(observation.photos), None)
                observation.encounter_type = (
                    (linked.encounter_type or "wild") if linked else "wild"
                )
        reconcile_linked_encounters(db)


def _ensure_species_metadata() -> None:
    """Migrate legacy tags into taxonomy, region, habitat and activity fields."""
    from .models import Species

    with SessionLocal.begin() as db:
        original_updates: dict[int, object] = {}
        for species in db.execute(select(Species)).scalars():
            previous_update = species.updated_at
            species.refresh_derived()
            if db.is_modified(species, include_collections=False):
                original_updates[species.id] = previous_update
        if not original_updates:
            return
        db.flush()
        for species_id, updated_at in original_updates.items():
            db.execute(
                update(Species)
                .where(Species.id == species_id)
                .values(updated_at=updated_at)
            )


def _ensure_achievement_baseline() -> None:
    """Synchronise existing progress without creating historical feed entries."""
    from .achievements import evaluate
    from .models import Profile

    with SessionLocal() as db:
        profile_ids = list(db.execute(select(Profile.id)).scalars())
        for profile_id in profile_ids:
            evaluate(db, profile_id, emit_activity=False)


def init_db() -> None:
    from . import models  # noqa: F401  (register mappers)

    if p := settings.sqlite_path:
        p.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    _ensure_columns()
    _ensure_default_profile()
    _ensure_shared_profile()
    _ensure_species_metadata()
    _ensure_linked_encounters()
    _ensure_achievement_baseline()
