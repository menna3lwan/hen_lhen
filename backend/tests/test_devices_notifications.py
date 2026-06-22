"""Device registration & notification tests."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestDeviceRegistration:
    async def test_register_device(self, client, patient_token):
        r = await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "test_fcm_token_12345678", "platform": "android", "device_name": "Pixel 8"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 201, r.text
        assert r.json()["message_ar"] == "تم تسجيل الجهاز"

    async def test_register_device_idempotent(self, client, patient_token):
        body = {"fcm_token": "test_fcm_token_12345678", "platform": "ios", "device_name": "iPhone"}
        r1 = await client.post("/api/v1/devices/register", json=body, headers={"Authorization": f"Bearer {patient_token}"})
        r2 = await client.post("/api/v1/devices/register", json=body, headers={"Authorization": f"Bearer {patient_token}"})
        assert r1.status_code == 201
        assert r2.status_code == 201  # Updates existing, no error

    async def test_register_device_invalid_platform(self, client, patient_token):
        r = await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "test_fcm_token_12345678", "platform": "windows"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 422

    async def test_register_device_short_token(self, client, patient_token):
        r = await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "short", "platform": "android"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 422

    async def test_unregister_device(self, client, patient_token):
        token = "test_fcm_unreg_12345678"
        await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": token, "platform": "android"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        r = await client.delete(
            f"/api/v1/devices/unregister?fcm_token={token}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
        assert r.json()["message_ar"] == "تم إلغاء تسجيل الجهاز"

    async def test_unregister_nonexistent_device(self, client, patient_token):
        """Should succeed silently (no error)."""
        r = await client.delete(
            "/api/v1/devices/unregister?fcm_token=nonexistent_token",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200

    async def test_no_auth(self, client):
        r = await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "test_fcm_token_12345678", "platform": "android"},
        )
        assert r.status_code in (401, 403)


class TestNotifications:
    async def test_list_notifications_empty(self, client, patient_token):
        r = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200

    async def test_mark_all_read(self, client, patient_token):
        r = await client.patch(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
