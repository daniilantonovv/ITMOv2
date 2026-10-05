"""Feature B — storage failure (503 when database is unavailable)."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_post_with_corrupted_database_returns_503(tmp_path, new_collection):
    """POST /api/collections returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.post("/api/collections", json=new_collection())

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_get_list_with_corrupted_database_returns_503(tmp_path):
    """GET /api/collections returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.get("/api/collections")

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_get_by_id_with_corrupted_database_returns_503(tmp_path):
    """GET /api/collections/{id} returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.get("/api/collections/1")

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_put_with_corrupted_database_returns_503(tmp_path, new_collection):
    """PUT /api/collections/{id} returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.put("/api/collections/1", json=new_collection())

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_delete_with_corrupted_database_returns_503(tmp_path):
    """DELETE /api/collections/{id} returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.delete("/api/collections/1")

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_get_categories_with_corrupted_database_returns_503(tmp_path):
    """GET /api/categories returns 503 when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.get("/api/categories")

    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_storage_error_does_not_expose_internal_details(tmp_path, new_collection):
    """503 response contains only the contract message, no SQLite details."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.post("/api/collections", json=new_collection())

    body = response.json()
    assert body == {"detail": "storage unavailable"}
    assert "sqlite" not in response.text.lower()
    assert str(db_path) not in response.text


def test_dashboard_loads_when_storage_unavailable(tmp_path):
    """GET / (dashboard) returns 200 even when database is corrupted."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))

    response = client.get("/")

    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.content or b"<html" in response.content


def test_storage_broken_while_running_returns_503(tmp_path, new_collection):
    """The database breaks after the app has started serving requests."""
    db_path = tmp_path / "live.db"
    client = TestClient(create_app(db_path=db_path))
    created = client.post("/api/collections", json=new_collection()).json()

    db_path.write_bytes(b"not a database" * 100)

    for response in [
        client.get("/api/collections"),
        client.get(f"/api/collections/{created['id']}"),
        client.post("/api/collections", json=new_collection()),
        client.get("/api/categories"),
    ]:
        assert response.status_code == 503
        assert response.json() == {"detail": "storage unavailable"}


def test_api_recovers_when_storage_is_repaired(tmp_path, new_collection):
    """A failure at startup is not permanent: a repaired database works without restart."""
    db_path = tmp_path / "repaired.db"
    db_path.write_text("not a database")
    client = TestClient(create_app(db_path=db_path))
    assert client.get("/api/collections").status_code == 503

    db_path.unlink()

    assert client.get("/api/collections").status_code == 200
    assert client.post("/api/collections", json=new_collection()).status_code == 201
