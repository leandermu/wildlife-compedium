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


def init_db() -> None:
    from . import models  # noqa: F401  (register mappers)

    if p := settings.sqlite_path:
        p.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    _ensure_columns()
    _ensure_default_profile()
