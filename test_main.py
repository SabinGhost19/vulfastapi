"""Unit tests for the demo FastAPI app.

Exercise the real endpoints with FastAPI's TestClient (uses httpx). The
TestClient context manager triggers the startup event, which seeds the
SQLite users table used by /users/search.
"""

from fastapi.testclient import TestClient

from main import app


def test_health_endpoints():
    with TestClient(app) as client:
        for path in ("/health", "/healthz", "/healthy"):
            resp = client.get(path)
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}


def test_users_search_returns_seeded_admin():
    with TestClient(app) as client:
        resp = client.get("/users/search", params={"username": "admin"})
        assert resp.status_code == 200
        body = resp.json()
        assert [1, "admin"] in body["results"]


def test_debug_eval_computes_expression():
    with TestClient(app) as client:
        resp = client.post("/debug/eval", json={"expr": "1 + 1"})
        assert resp.status_code == 200
        assert resp.json() == {"result": "2"}


def test_stats_computes_descriptive_statistics():
    with TestClient(app) as client:
        resp = client.post("/stats", json={"values": [2, 4, 6, 8]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 4
        assert body["sum"] == 20.0
        assert body["mean"] == 5.0
        assert body["min"] == 2.0
        assert body["max"] == 8.0


def test_stats_rejects_empty_list():
    with TestClient(app) as client:
        resp = client.post("/stats", json={"values": []})
        assert resp.status_code == 400


def test_stats_rejects_non_numeric():
    with TestClient(app) as client:
        resp = client.post("/stats", json={"values": ["a", "b"]})
        assert resp.status_code == 400
