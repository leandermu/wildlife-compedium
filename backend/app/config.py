from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Central configuration. Everything storage- or DB-related is swappable
    through env vars so the app can move from local SQLite + disk to
    Postgres + cloud storage without code changes."""

    model_config = SettingsConfigDict(
        env_prefix="WC_", env_file=BASE_DIR / ".env", extra="ignore"
    )

    database_url: str = "sqlite:///./data/compendium.db"

    storage_backend: str = "local"  # "local" | "s3" (s3 = future)
    storage_local_dir: str = "./data/media"
    media_base_url: str = "/media"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def local_media_path(self) -> Path:
        p = Path(self.storage_local_dir)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p

    @property
    def sqlite_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite"):
            return None
        raw = self.database_url.split("///")[-1]
        p = Path(raw)
        return p if p.is_absolute() else BASE_DIR / p


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
