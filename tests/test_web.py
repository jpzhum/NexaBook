from pathlib import Path
import re

from fastapi.testclient import TestClient

from nexabook.config import get_settings


def csrf_from(response) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)


def build_client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "web.db"))
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    get_settings.cache_clear()
    from nexabook.web import create_app
    return TestClient(create_app())


def build_production_client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "s" * 32)
    monkeypatch.setenv("ADMIN_USERNAME", "portfolio-admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "synthetic-password")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "web.db"))
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path / "exports"))
    get_settings.cache_clear()
    from nexabook.web import create_app
    return TestClient(create_app(), base_url="https://testserver")


def test_health_and_empty_app_start(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_state_change_rejects_missing_csrf(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    response = client.post("/exports", data={"file_type": "csv"})
    assert response.status_code == 422


def test_invalid_isbn_returns_validation_error(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    token = client.get("/").cookies.get("session")
    assert token
    csrf = csrf_from(client.get("/"))
    response = client.post("/books/enrich", data={"isbn": "invalid", "csrf": csrf})
    assert response.status_code == 422


def test_invalid_export_type_returns_bad_request(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    csrf = csrf_from(client.get("/"))
    response = client.post("/exports", data={"file_type": "pdf", "csrf": csrf})
    assert response.status_code == 400


def test_production_requires_login_and_sets_secure_session_cookie(tmp_path, monkeypatch):
    client = build_production_client(tmp_path, monkeypatch)
    redirect = client.get("/", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == "/login"
    assert client.get("/health").status_code == 200
    assert client.get("/api/docs").status_code == 200
    login_page = client.get("/login")
    csrf = csrf_from(login_page)
    response = client.post(
        "/login",
        data={"username": "portfolio-admin", "password": "synthetic-password", "csrf": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 303
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie
    assert client.get("/").status_code == 200


def test_login_throttles_repeated_failures(tmp_path, monkeypatch):
    client = build_production_client(tmp_path, monkeypatch)
    for _ in range(5):
        csrf = csrf_from(client.get("/login"))
        assert client.post("/login", data={"username": "wrong", "password": "wrong", "csrf": csrf}).status_code == 401
    csrf = csrf_from(client.get("/login"))
    assert client.post("/login", data={"username": "wrong", "password": "wrong", "csrf": csrf}).status_code == 429
