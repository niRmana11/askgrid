from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.datasets import get_session_store
from app.main import app
from app.services.session_store import EphemeralSessionStore

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def isolated_client(tmp_path: Path) -> Iterator[tuple[TestClient, EphemeralSessionStore]]:
    store = EphemeralSessionStore(base_dir=tmp_path, ttl_minutes=60)
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        yield TestClient(app), store
    finally:
        app.dependency_overrides.clear()


def test_sample_load_get_and_delete_lifecycle(
    isolated_client: tuple[TestClient, EphemeralSessionStore],
) -> None:
    client, store = isolated_client

    create_res = client.post("/api/v1/datasets/sample")
    assert create_res.status_code == 201
    data = create_res.json()
    session_id = data["session_id"]
    assert data["is_sample"] is True
    assert data["profile"]["row_count"] == 24
    assert "never raw row values" in data["privacy_notice"]

    # GET returns same session
    get_res = client.get(f"/api/v1/datasets/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["session_id"] == session_id

    # DELETE removes files from disk immediately
    del_res = client.delete(f"/api/v1/datasets/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True
    assert list(store.base_dir.iterdir()) == []

    # Subsequent GET returns 404
    assert client.get(f"/api/v1/datasets/{session_id}").status_code == 404


def test_upload_messy_csv_and_sanitize_malicious_filename(
    isolated_client: tuple[TestClient, EphemeralSessionStore],
) -> None:
    client, _ = isolated_client
    messy_bytes = (FIXTURES / "messy_sales.csv").read_bytes()

    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("../../etc/messy_sales.csv", messy_bytes, "text/csv")},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["filename"] == "messy_sales.csv"
    assert body["profile"]["delimiter"] == ";"
    assert body["profile"]["duplicate_row_count"] == 1


def test_upload_rejects_binary_and_invalid_session_ids(
    isolated_client: tuple[TestClient, EphemeralSessionStore],
) -> None:
    client, _ = isolated_client

    bad_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("fake.csv", b"\x89PNG\r\n\x1a\n\x00\x00IHDR", "text/csv")},
    )
    assert bad_res.status_code == 400
    assert "Binary" in bad_res.json()["detail"]

    # Path traversal or non-UUID session ID cleanly returns 404
    assert client.get("/api/v1/datasets/not-a-valid-uuid").status_code == 404


def test_expired_session_auto_deletes(tmp_path: Path) -> None:
    store = EphemeralSessionStore(base_dir=tmp_path, ttl_minutes=0)
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        client = TestClient(app)
        res = client.post("/api/v1/datasets/sample")
        assert res.status_code == 201
        session_id = res.json()["session_id"]

        # Because ttl_minutes=0, session is already expired -> 404 & files purged
        assert client.get(f"/api/v1/datasets/{session_id}").status_code == 404
        assert list(store.base_dir.iterdir()) == []
    finally:
        app.dependency_overrides.clear()
