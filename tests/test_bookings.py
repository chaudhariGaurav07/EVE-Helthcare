import uuid
from datetime import datetime, timedelta, timezone


def _future_time():
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


def _past_time():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


class TestCreateBooking:
    def test_create_booking(self, client, auth_headers, sample_centre, sample_test):
        resp = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PENDING"
        assert float(data["amount"]) == float(sample_test["price"])

    def test_create_booking_past_time(self, client, auth_headers, sample_centre, sample_test):
        resp = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _past_time(),
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "future" in resp.json()["detail"].lower()

    def test_create_booking_unauthenticated(self, client, sample_centre, sample_test):
        resp = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        })
        assert resp.status_code == 401

    def test_create_booking_nonexistent_test(self, client, auth_headers, sample_centre):
        resp = client.post("/bookings/", json={
            "test_id": str(uuid.uuid4()),
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_create_booking_nonexistent_centre(self, client, auth_headers, sample_test):
        resp = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": str(uuid.uuid4()),
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_create_booking_test_centre_mismatch(self, client, auth_headers, sample_test):
        other_centre = client.post("/centres/", json={
            "name": "Other Centre",
            "location": "Delhi",
        }, headers=auth_headers).json()
        resp = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": other_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "not available" in resp.json()["detail"].lower()


class TestListBookings:
    def test_list_my_bookings(self, client, auth_headers, sample_centre, sample_test):
        client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        resp = client.get("/bookings/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_bookings_does_not_show_others(self, client, auth_headers, second_user_headers, sample_centre, sample_test):
        client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        resp = client.get("/bookings/", headers=second_user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_list_bookings_filter_by_status(self, client, auth_headers, sample_centre, sample_test):
        client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers)
        resp = client.get("/bookings/?status=CONFIRMED", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestGetBooking:
    def test_get_booking_by_id(self, client, auth_headers, sample_centre, sample_test):
        booking = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers).json()
        resp = client.get(f"/bookings/{booking['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == booking["id"]

    def test_get_booking_not_found(self, client, auth_headers):
        resp = client.get(f"/bookings/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_booking_forbidden(self, client, auth_headers, second_user_headers, sample_centre, sample_test):
        booking = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers).json()
        resp = client.get(f"/bookings/{booking['id']}", headers=second_user_headers)
        assert resp.status_code == 403


class TestCancelBooking:
    def test_cancel_pending_booking(self, client, auth_headers, sample_centre, sample_test):
        booking = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers).json()
        resp = client.patch(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancel_already_cancelled(self, client, auth_headers, sample_centre, sample_test):
        booking = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers).json()
        client.patch(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
        resp = client.patch(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
        assert resp.status_code == 400

    def test_cancel_other_users_booking(self, client, auth_headers, second_user_headers, sample_centre, sample_test):
        booking = client.post("/bookings/", json={
            "test_id": sample_test["id"],
            "centre_id": sample_centre["id"],
            "appointment_time": _future_time(),
        }, headers=auth_headers).json()
        resp = client.patch(f"/bookings/{booking['id']}/cancel", headers=second_user_headers)
        assert resp.status_code == 403
