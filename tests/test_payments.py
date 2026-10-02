import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


def _future_time():
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


def _create_booking(client, auth_headers, sample_centre, sample_test):
    resp = client.post("/bookings/", json={
        "test_id": sample_test["id"],
        "centre_id": sample_centre["id"],
        "appointment_time": _future_time(),
    }, headers=auth_headers)
    return resp.json()


class TestInitiatePayment:
    @patch("app.api.payments.random.random", return_value=0.5)
    def test_payment_success(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        resp = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["transaction_id"].startswith("txn_")

        booking_resp = client.get(f"/bookings/{booking['id']}", headers=auth_headers)
        assert booking_resp.json()["status"] == "CONFIRMED"

    @patch("app.api.payments.random.random", return_value=0.95)
    def test_payment_failure(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        resp = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["status"] == "FAILED"

        booking_resp = client.get(f"/bookings/{booking['id']}", headers=auth_headers)
        assert booking_resp.json()["status"] == "FAILED"

    @patch("app.api.payments.random.random", return_value=0.5)
    def test_duplicate_payment_rejected(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers)
        resp = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers)
        assert resp.status_code == 400

    def test_payment_nonexistent_booking(self, client, auth_headers):
        resp = client.post("/payments/", json={"booking_id": str(uuid.uuid4())}, headers=auth_headers)
        assert resp.status_code == 404

    @patch("app.api.payments.random.random", return_value=0.5)
    def test_payment_forbidden_for_other_user(self, mock_rand, client, auth_headers, second_user_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        resp = client.post("/payments/", json={"booking_id": booking["id"]}, headers=second_user_headers)
        assert resp.status_code == 403

    @patch("app.api.payments.random.random", return_value=0.5)
    def test_payment_for_cancelled_booking(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        client.patch(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
        resp = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers)
        assert resp.status_code == 400


class TestWebhook:
    @patch("app.api.payments.random.random", return_value=0.5)
    def test_webhook_idempotent(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        payment = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers).json()

        webhook_payload = {
            "transaction_id": payment["transaction_id"],
            "status": "SUCCESS",
            "idempotency_key": f"webhook_{payment['transaction_id']}_1",
        }
        resp1 = client.post("/payments/webhook/", json=webhook_payload)
        assert resp1.status_code == 200

        resp2 = client.post("/payments/webhook/", json=webhook_payload)
        assert resp2.status_code == 200
        assert "already" in resp2.json()["message"].lower()

    def test_webhook_invalid_transaction(self, client):
        resp = client.post("/payments/webhook/", json={
            "transaction_id": "txn_nonexistent",
            "status": "SUCCESS",
            "idempotency_key": "key_123",
        })
        assert resp.status_code == 404

    def test_webhook_missing_fields(self, client):
        resp = client.post("/payments/webhook/", json={"transaction_id": "txn_abc"})
        assert resp.status_code == 422


class TestGetPayment:
    @patch("app.api.payments.random.random", return_value=0.5)
    def test_get_payment(self, mock_rand, client, auth_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        payment = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers).json()
        resp = client.get(f"/payments/{payment['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == payment["id"]

    @patch("app.api.payments.random.random", return_value=0.5)
    def test_get_payment_forbidden(self, mock_rand, client, auth_headers, second_user_headers, sample_centre, sample_test):
        booking = _create_booking(client, auth_headers, sample_centre, sample_test)
        payment = client.post("/payments/", json={"booking_id": booking["id"]}, headers=auth_headers).json()
        resp = client.get(f"/payments/{payment['id']}", headers=second_user_headers)
        assert resp.status_code == 403

    def test_get_payment_not_found(self, client, auth_headers):
        resp = client.get(f"/payments/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404
