from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_env: str
    secret_key: str
    admin_username: str | None
    admin_password: str | None
    database_path: Path
    export_dir: Path
    google_books_api_key: str | None
    openai_api_key: str | None
    openai_model: str
    enable_openai_fallback: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    settings = Settings(
        app_env=app_env,
        secret_key=os.getenv("SECRET_KEY", "development-only-secret"),
        admin_username=os.getenv("ADMIN_USERNAME") or None,
        admin_password=os.getenv("ADMIN_PASSWORD") or None,
        database_path=Path(os.getenv("DATABASE_PATH", ROOT / "data" / "nexabook.db")).resolve(),
        export_dir=Path(os.getenv("EXPORT_DIR", ROOT / "exports")).resolve(),
        google_books_api_key=os.getenv("GOOGLE_BOOKS_API_KEY") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        enable_openai_fallback=os.getenv("ENABLE_OPENAI_FALLBACK", "false").lower() in {"1", "true", "yes"},
    )
    if app_env == "production" and (
        len(settings.secret_key) < 32 or not settings.admin_username or not settings.admin_password
    ):
        raise RuntimeError("Production requires SECRET_KEY (at least 32 characters), ADMIN_USERNAME and ADMIN_PASSWORD")
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings
