import io
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["UPLOAD_FOLDER"] = tempfile.mkdtemp()

from app import app, seed_database  # noqa: E402
from models import init_db  # noqa: E402


@pytest.fixture
def client():
    init_db()
    seed_database()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def login(client, email="alice@ajaia.com", password="password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.get_json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={"email": "alice@ajaia.com", "password": "wrong"})
    assert res.status_code == 401


def test_create_and_update_document(client):
    token = login(client)
    headers = auth_headers(token)

    create_res = client.post(
        "/api/documents",
        json={"title": "Test Doc", "content": "<p>Hello <strong>world</strong></p>"},
        headers=headers,
    )
    assert create_res.status_code == 201
    doc = create_res.get_json()["document"]
    assert doc["title"] == "Test Doc"
    assert "<strong>world</strong>" in doc["content"]

    get_res = client.get(f"/api/documents/{doc['id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["access_type"] == "owner"

    update_res = client.put(
        f"/api/documents/{doc['id']}",
        json={"title": "Renamed Doc", "content": "<p>Updated</p>"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.get_json()["document"]["title"] == "Renamed Doc"


def test_document_sharing_flow(client):
    alice_token = login(client, "alice@ajaia.com")
    bob_token = login(client, "bob@ajaia.com")

    create_res = client.post(
        "/api/documents",
        json={"title": "Shared Doc", "content": "<p>Share me</p>"},
        headers=auth_headers(alice_token),
    )
    doc_id = create_res.get_json()["document"]["id"]

    bob_list_before = client.get("/api/documents", headers=auth_headers(bob_token))
    assert len(bob_list_before.get_json()["shared"]) == 0

    share_res = client.post(
        f"/api/documents/{doc_id}/share",
        json={"user_id": 2, "permission": "edit"},
        headers=auth_headers(alice_token),
    )
    assert share_res.status_code == 200

    bob_get = client.get(f"/api/documents/{doc_id}", headers=auth_headers(bob_token))
    assert bob_get.status_code == 200
    assert bob_get.get_json()["access_type"] == "edit"

    bob_list_after = client.get("/api/documents", headers=auth_headers(bob_token))
    assert len(bob_list_after.get_json()["shared"]) == 1


def test_import_md_file(client):
    token = login(client)
    data = {
        "file": (io.BytesIO(b"# Heading\n\nHello from file"), "notes.md"),
    }
    res = client.post(
        "/api/documents/import",
        data=data,
        content_type="multipart/form-data",
        headers=auth_headers(token),
    )
    assert res.status_code == 201
    doc = res.get_json()["document"]
    assert "notes" in doc["title"].lower()
    assert "<h1>Heading</h1>" in doc["content"]
