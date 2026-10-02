class TestSignup:
    def test_signup_success(self, client):
        resp = client.post("/auth/signup", json={
            "email": "new@example.com",
            "password": "password123",
            "full_name": "New User",
            "phone": "+919876543210",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password_hash" not in data

    def test_signup_duplicate_email(self, client):
        payload = {
            "email": "dup@example.com",
            "password": "password123",
            "full_name": "User One",
        }
        client.post("/auth/signup", json=payload)
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 409

    def test_signup_invalid_email(self, client):
        resp = client.post("/auth/signup", json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Bad Email",
        })
        assert resp.status_code == 422

    def test_signup_short_password(self, client):
        resp = client.post("/auth/signup", json={
            "email": "short@example.com",
            "password": "123",
            "full_name": "Short Pass",
        })
        assert resp.status_code == 422

    def test_signup_missing_name(self, client):
        resp = client.post("/auth/signup", json={
            "email": "noname@example.com",
            "password": "password123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post("/auth/signup", json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
        })
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert resp.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/auth/signup", json={
            "email": "wrong@example.com",
            "password": "password123",
            "full_name": "Wrong Pass",
        })
        resp = client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", json={
            "email": "ghost@example.com",
            "password": "password123",
        })
        assert resp.status_code == 401


class TestMe:
    def test_get_me_authenticated(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401
