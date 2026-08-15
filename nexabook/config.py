from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
VALID_APP_ENVS = {"development", "production"}


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
    if app_env not in VALID_APP_ENVS:
        raise RuntimeError("APP_ENV must be 'development' or 'production'")

    configured_secret_key = os.getenv("SECRET_KEY") or ""
    admin_username = os.getenv("ADMIN_USERNAME", "").strip() or None
    admin_password = os.getenv("ADMIN_PASSWORD") or None
    openai_fallback_flag = os.getenv("ENABLE_OPENAI_FALLBACK", "false").strip().lower()
    settings = Settings(
        app_env=app_env,
        secret_key=configured_secret_key or "development-only-secret",
        admin_username=admin_username,
        admin_password=admin_password,
        database_path=Path(os.getenv("DATABASE_PATH", ROOT / "data" / "nexabook.db")).resolve(),
        export_dir=Path(os.getenv("EXPORT_DIR", ROOT / "exports")).resolve(),
        google_books_api_key=os.getenv("GOOGLE_BOOKS_API_KEY") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        enable_openai_fallback=openai_fallback_flag in {"1", "true", "yes"},
    )
    if app_env == "production" and (
        len(settings.secret_key) < 32 or not settings.admin_username or not settings.admin_password
    ):
        raise RuntimeError("Production requires SECRET_KEY (at least 32 characters), ADMIN_USERNAME and ADMIN_PASSWORD")
    if app_env == "development" and (settings.admin_username or settings.admin_password) and (
        len(configured_secret_key) < 32 or not settings.admin_username or not settings.admin_password
    ):
        raise RuntimeError(
            "Development authentication requires SECRET_KEY (at least 32 characters), "
            "ADMIN_USERNAME and ADMIN_PASSWORD"
        )
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings
