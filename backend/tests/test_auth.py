CREDS = {"email": "owner@example.com", "password": "correct-horse"}


def setup_owner(c):
    assert c.post("/api/auth/setup", json=CREDS).status_code == 200


def test_setup_once_and_owner_role(client):
    assert client.get("/api/auth/status").json() == {"needs_setup": True}
    setup_owner(client)
    assert client.get("/api/auth/me").json()["role"] == "owner"
    assert client.get("/api/auth/status").json() == {"needs_setup": False}
    assert client.post("/api/auth/setup", json={**CREDS, "email": "x@example.com"}).status_code == 409


def test_protected_routes_need_login(client):
    assert client.get("/api/events").status_code == 401
    assert client.get("/api/users").status_code == 401


def test_login_logout_and_bad_password(client):
    setup_owner(client)
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={**CREDS, "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json=CREDS).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_session_cookie_is_httponly(client):
    r = client.post("/api/auth/setup", json=CREDS)
    assert "httponly" in r.headers["set-cookie"].lower()


def test_writes_require_csrf_header(client):
    from fastapi.testclient import TestClient
    from app.main import app
    assert TestClient(app).post("/api/auth/login", json=CREDS).status_code == 403


def test_owner_creates_admin_and_admin_cannot(client):
    setup_owner(client)
    admin = {"email": "admin@example.com", "password": "another-pass"}
    assert client.post("/api/users", json=admin).status_code == 201
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json=admin)
    assert client.post("/api/users", json={**admin, "email": "b@example.com"}).status_code == 403
    assert client.get("/api/events").status_code == 200


def test_event_crud(client):
    setup_owner(client)
    r = client.post("/api/events", json={"name": "החתונה של דני", "date": "2026-12-01"})
    assert r.status_code == 201 and r.json()["default_language"] == "he"
    eid = r.json()["id"]
    assert client.put(f"/api/events/{eid}", json={"name": "New", "venue": "Hall"}).json()["venue"] == "Hall"
    assert len(client.get("/api/events").json()) == 1
    assert client.delete(f"/api/events/{eid}").status_code == 204
    assert client.get(f"/api/events/{eid}").status_code == 404
