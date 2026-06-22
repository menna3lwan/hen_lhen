"""Payment E2E tests — initiation, webhook, history, refund, auth, edge cases."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Payment Initiation ──

class TestPaymentInitiation:
    async def test_initiate_payment_success(self, client: AsyncClient, patient_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["status"] == "pending"
        assert data["amount"] == 200.0
        assert data["currency"] == "EGP"
        assert data["payment_url"] is not None
        assert data["transaction_id"] is not None

    async def test_initiate_payment_duplicate_blocked(self, client, patient_token, pending_appointment):
        """Second payment for same appointment should fail."""
        body = {"appointment_id": str(pending_appointment.id), "payment_method": "card"}
        r1 = await client.post("/api/v1/payments/initiate", json=body, headers={"Authorization": f"Bearer {patient_token}"})
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/payments/initiate", json=body, headers={"Authorization": f"Bearer {patient_token}"})
        assert r2.status_code == 409
        assert r2.json()["detail"]["code"] == "PAYMENT_ALREADY_EXISTS"

    async def test_initiate_payment_invalid_method(self, client, patient_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "bitcoin"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 422  # Pydantic validation

    async def test_initiate_payment_nonexistent_appointment(self, client, patient_token):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(uuid.uuid4()), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 404

    async def test_initiate_payment_not_your_appointment(self, client, doctor_token, pending_appointment):
        """Doctor should not be able to initiate patient's payment."""
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        # Doctor role can't access patient-only endpoint
        assert r.status_code == 403

    async def test_initiate_payment_no_auth(self, client, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
        )
        assert r.status_code in (401, 403)

    async def test_initiate_fawry_method(self, client, patient_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "fawry"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 201

    async def test_initiate_wallet_method(self, client, patient_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "wallet"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        # If fawry already created, this may be 409 (duplicate). Either 201 or 409 is fine.
        assert r.status_code in (201, 409)


# ── Webhook Processing ──

class TestPaymentWebhook:
    async def test_webhook_completed(self, client, patient_token, pending_appointment):
        # First initiate
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        txn_id = r.json()["transaction_id"]

        # Then webhook
        r2 = await client.post("/api/v1/payments/webhook", json={
            "transaction_id": txn_id,
            "status": "completed",
        })
        assert r2.status_code == 200
        assert r2.json()["status"] == "completed"

    async def test_webhook_failed(self, client, patient_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        txn_id = r.json()["transaction_id"]

        r2 = await client.post("/api/v1/payments/webhook", json={
            "transaction_id": txn_id, "status": "failed",
        })
        assert r2.status_code == 200
        assert r2.json()["status"] == "failed"

    async def test_webhook_nonexistent_transaction(self, client):
        r = await client.post("/api/v1/payments/webhook", json={
            "transaction_id": "fake_txn_123", "status": "completed",
        })
        assert r.status_code == 404


# ── Payment History ──

class TestPaymentHistory:
    async def test_history_empty(self, client, patient_token):
        r = await client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
        assert r.json()["data"] == []
        assert r.json()["meta"]["total"] == 0

    async def test_history_after_payment(self, client, patient_token, pending_appointment):
        await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        r = await client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
        assert r.json()["meta"]["total"] == 1
        assert r.json()["data"][0]["amount"] == 200.0

    async def test_history_no_auth(self, client):
        r = await client.get("/api/v1/payments/history")
        assert r.status_code in (401, 403)

    async def test_history_doctor_cannot_access(self, client, doctor_token):
        r = await client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r.status_code == 403


# ── Refund ──

class TestPaymentRefund:
    async def test_refund_requires_admin(self, client, patient_token, pending_appointment):
        # Initiate + complete
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        pid = r.json()["payment_id"]

        # Patient tries refund → 403
        r2 = await client.post(
            "/api/v1/payments/refund",
            json={"payment_id": pid},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r2.status_code == 403

    async def test_refund_not_completed_payment(self, client, patient_token, admin_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        pid = r.json()["payment_id"]

        # Refund pending payment → 400
        r2 = await client.post(
            "/api/v1/payments/refund",
            json={"payment_id": pid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r2.status_code == 400
        assert r2.json()["detail"]["code"] == "PAYMENT_NOT_COMPLETED"

    async def test_full_refund_success(self, client, patient_token, admin_token, pending_appointment):
        # Initiate
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        pid = r.json()["payment_id"]
        txn_id = r.json()["transaction_id"]

        # Complete via webhook
        await client.post("/api/v1/payments/webhook", json={
            "transaction_id": txn_id, "status": "completed",
        })

        # Full refund
        r3 = await client.post(
            "/api/v1/payments/refund",
            json={"payment_id": pid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r3.status_code == 200
        assert r3.json()["status"] == "refunded"
        assert r3.json()["refund_amount"] == 200.0

    async def test_partial_refund(self, client, patient_token, admin_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        pid = r.json()["payment_id"]
        txn_id = r.json()["transaction_id"]
        await client.post("/api/v1/payments/webhook", json={"transaction_id": txn_id, "status": "completed"})

        r3 = await client.post(
            "/api/v1/payments/refund",
            json={"payment_id": pid, "amount": 50.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r3.status_code == 200
        assert r3.json()["refund_amount"] == 50.0

    async def test_refund_exceeds_amount(self, client, patient_token, admin_token, pending_appointment):
        r = await client.post(
            "/api/v1/payments/initiate",
            json={"appointment_id": str(pending_appointment.id), "payment_method": "card"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        pid = r.json()["payment_id"]
        txn_id = r.json()["transaction_id"]
        await client.post("/api/v1/payments/webhook", json={"transaction_id": txn_id, "status": "completed"})

        r3 = await client.post(
            "/api/v1/payments/refund",
            json={"payment_id": pid, "amount": 9999.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r3.status_code == 400
        assert r3.json()["detail"]["code"] == "REFUND_EXCEEDS_AMOUNT"
