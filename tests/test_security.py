from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from nexabook.security import LoginLimiter, csrf_token, verify_csrf
from nexabook.config import get_settings


def test_csrf_token_is_stable_and_required():
    request = SimpleNamespace(session={})
    token = csrf_token(request)
    assert csrf_token(request) == token
    verify_csrf(request, token)
    with pytest.raises(HTTPException):
        verify_csrf(request, "wrong")


def test_login_limiter_blocks_after_bounded_failures():
    limiter = LoginLimiter(attempts=2, window_seconds=60)
    assert limiter.allowed("demo")
    limiter.failure("demo"); limiter.failure("demo")
    assert not limiter.allowed("demo")
    limiter.success("demo")
    assert limiter.allowed("demo")


def test_production_rejects_weak_session_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "synthetic-password")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()
    get_settings.cache_clear()


@pytest.mark.parametrize("missing_variable", ["ADMIN_USERNAME", "ADMIN_PASSWORD"])
def test_production_requires_both_credentials(monkeypatch, missing_variable):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "s" * 32)
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "synthetic-password")
    monkeypatch.delenv(missing_variable)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        get_settings()

    get_settings.cache_clear()


def test_development_authentication_requires_complete_strong_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "synthetic-password")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        get_settings()

    get_settings.cache_clear()


def test_invalid_environment_name_fails_closed(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prodution")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        get_settings()

    get_settings.cache_clear()


def test_blank_development_secret_uses_nonempty_local_default(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", " true ")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.secret_key == "development-only-secret"
    assert settings.enable_openai_fallback is True
    get_settings.cache_clear()
