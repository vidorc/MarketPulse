"""Auth + RBAC: registration, login, token validation, and role enforcement.

Uses ``raw_client`` (no auth override) so the real Bearer-token flow and role
guards are exercised end to end.
"""
from __future__ import annotations


def _register(client, email, password="password123", full_name=None):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def _login(client, email, password="password123"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


class TestRegistration:
    def test_register_creates_viewer_and_returns_user(self, raw_client):
        res = _register(raw_client, "newbie@test.io")
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "newbie@test.io"
        assert body["role"] == "viewer"  # self-registration is always viewer
        assert "hashed_password" not in body

    def test_register_ignores_requested_elevated_role(self, raw_client):
        res = raw_client.post(
            "/api/v1/auth/register",
            json={"email": "sneaky@test.io", "password": "password123", "role": "admin"},
        )
        assert res.status_code == 201
        assert res.json()["role"] == "viewer"

    def test_duplicate_email_conflicts(self, raw_client):
        _register(raw_client, "dupe@test.io")
        res = _register(raw_client, "dupe@test.io")
        assert res.status_code == 409

    def test_short_password_rejected(self, raw_client):
        res = _register(raw_client, "x@test.io", password="short")
        assert res.status_code == 422


class TestLogin:
    def test_login_returns_bearer_token(self, raw_client):
        _register(raw_client, "user@test.io")
        res = _login(raw_client, "user@test.io")
        assert res.status_code == 200
        body = res.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    def test_wrong_password_is_401(self, raw_client):
        _register(raw_client, "user@test.io")
        res = _login(raw_client, "user@test.io", password="wrongpass")
        assert res.status_code == 401

    def test_unknown_email_is_401_same_message(self, raw_client):
        res = _login(raw_client, "ghost@test.io")
        assert res.status_code == 401
        # Don't leak which accounts exist.
        assert res.json()["detail"] == "Incorrect email or password."

    def test_disabled_account_cannot_login(self, raw_client, make_user):
        make_user(email="off@test.io", role="viewer", is_active=False)
        res = _login(raw_client, "off@test.io")
        assert res.status_code == 403


class TestMe:
    def test_me_requires_token(self, raw_client):
        res = raw_client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_me_returns_current_user(self, raw_client, make_user, auth_header):
        user = make_user(email="me@test.io", role="analyst")
        res = raw_client.get("/api/v1/auth/me", headers=auth_header(user))
        assert res.status_code == 200
        assert res.json()["email"] == "me@test.io"
        assert res.json()["role"] == "analyst"

    def test_garbage_token_is_401(self, raw_client):
        res = raw_client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert res.status_code == 401


class TestRoleGuards:
    def test_viewer_cannot_list_users(self, raw_client, make_user, auth_header):
        viewer = make_user(email="v@test.io", role="viewer")
        res = raw_client.get("/api/v1/auth/users", headers=auth_header(viewer))
        assert res.status_code == 403

    def test_admin_can_list_users(self, raw_client, make_user, auth_header):
        admin = make_user(email="a@test.io", role="admin")
        res = raw_client.get("/api/v1/auth/users", headers=auth_header(admin))
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    def test_admin_can_create_user_with_role(self, raw_client, make_user, auth_header):
        admin = make_user(email="boss@test.io", role="admin")
        res = raw_client.post(
            "/api/v1/auth/users",
            headers=auth_header(admin),
            json={"email": "hire@test.io", "password": "password123", "role": "analyst"},
        )
        assert res.status_code == 201
        assert res.json()["role"] == "analyst"

    def test_viewer_cannot_upload(self, raw_client, make_user, auth_header):
        viewer = make_user(email="ro@test.io", role="viewer")
        res = raw_client.post(
            "/api/v1/articles/upload",
            headers=auth_header(viewer),
            files={"file": ("n.csv", b"title\nx\n", "text/csv")},
        )
        assert res.status_code == 403

    def test_analyst_can_reach_upload(self, raw_client, make_user, auth_header):
        analyst = make_user(email="rw@test.io", role="analyst")
        res = raw_client.post(
            "/api/v1/articles/upload",
            headers=auth_header(analyst),
            files={"file": ("n.csv", b"title,article_text\nHi,body\n", "text/csv")},
        )
        # Reaches the handler (not 401/403); validation outcome is 200.
        assert res.status_code == 200

    def test_unauthenticated_list_articles_is_401(self, raw_client):
        res = raw_client.get("/api/v1/articles")
        assert res.status_code == 401
