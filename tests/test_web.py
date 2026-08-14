from pathlib import Path

from fastapi.testclient import TestClient

from nexabook.config import get_settings


def build_client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "web.db"))
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    get_settings.cache_clear()
    from nexabook.web import create_app
    return TestClient(create_app())


def test_health_and_empty_app_start(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_state_change_rejects_missing_csrf(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    response = client.post("/exports", data={"file_type": "csv"})
    assert response.status_code == 422
