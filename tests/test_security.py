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
