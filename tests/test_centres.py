import uuid


class TestCreateCentre:
    def test_create_centre(self, client, auth_headers):
        resp = client.post("/centres/", json={
            "name": "New Diagnostics",
            "location": "Mumbai",
            "address": "Andheri West",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Diagnostics"

    def test_create_centre_unauthenticated(self, client):
        resp = client.post("/centres/", json={
            "name": "Unauth Centre",
            "location": "Delhi",
        })
        assert resp.status_code == 401

    def test_create_centre_missing_fields(self, client, auth_headers):
        resp = client.post("/centres/", json={"name": "Incomplete"}, headers=auth_headers)
        assert resp.status_code == 422


class TestListCentres:
    def test_list_centres(self, client, sample_centre):
        resp = client.get("/centres/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_centres_filter_location(self, client, auth_headers):
        client.post("/centres/", json={"name": "BLR Centre", "location": "Bangalore"}, headers=auth_headers)
        client.post("/centres/", json={"name": "DEL Centre", "location": "Delhi"}, headers=auth_headers)
        resp = client.get("/centres/?location=Bangalore")
        assert resp.status_code == 200
        for c in resp.json():
            assert "bangalore" in c["location"].lower()

    def test_list_centres_pagination(self, client, auth_headers):
        for i in range(5):
            client.post("/centres/", json={"name": f"Centre {i}", "location": "Test"}, headers=auth_headers)
        resp = client.get("/centres/?page=1&size=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetCentre:
    def test_get_centre_by_id(self, client, sample_centre):
        resp = client.get(f"/centres/{sample_centre['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sample_centre["id"]

    def test_get_centre_not_found(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/centres/{fake_id}")
        assert resp.status_code == 404

    def test_get_centre_invalid_uuid(self, client):
        resp = client.get("/centres/not-a-uuid")
        assert resp.status_code == 422


class TestAddTest:
    def test_add_test_to_centre(self, client, auth_headers, sample_centre):
        resp = client.post(f"/centres/{sample_centre['id']}/tests", json={
            "name": "X-Ray",
            "description": "Chest X-Ray",
            "price": 300.00,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "X-Ray"
        assert float(resp.json()["price"]) == 300.00

    def test_add_test_invalid_price(self, client, auth_headers, sample_centre):
        resp = client.post(f"/centres/{sample_centre['id']}/tests", json={
            "name": "Cheap Test",
            "price": -100,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_add_test_to_nonexistent_centre(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/centres/{fake_id}/tests", json={
            "name": "Ghost Test",
            "price": 500,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_list_tests_for_centre(self, client, auth_headers, sample_centre):
        client.post(f"/centres/{sample_centre['id']}/tests", json={
            "name": "Test A", "price": 100,
        }, headers=auth_headers)
        client.post(f"/centres/{sample_centre['id']}/tests", json={
            "name": "Test B", "price": 200,
        }, headers=auth_headers)
        resp = client.get(f"/centres/{sample_centre['id']}/tests")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
