"""Chat E2E tests — rooms, messages, read receipts, close, auth."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestChatRooms:
    async def test_create_room_for_confirmed_appointment(self, client, patient_token, confirmed_appointment):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["status"] == "active"
        assert data["patient_name"] is not None
        assert data["doctor_name"] is not None

    async def test_create_room_idempotent(self, client, patient_token, confirmed_appointment):
        """Getting room twice returns same room."""
        r1 = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        r2 = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r1.json()["id"] == r2.json()["id"]

    async def test_create_room_pending_appointment_rejected(self, client, patient_token, pending_appointment):
        """Cannot create chat for unconfirmed appointment."""
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={pending_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "APPOINTMENT_NOT_CONFIRMED"

    async def test_create_room_nonexistent_appointment(self, client, patient_token):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={uuid.uuid4()}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 404

    async def test_list_rooms_patient(self, client, patient_token, confirmed_appointment):
        # Create a room first
        await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        r = await client.get(
            "/api/v1/chat/rooms",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_list_rooms_doctor(self, client, doctor_token, patient_token, confirmed_appointment):
        # Patient creates room
        await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        # Doctor sees it
        r = await client.get(
            "/api/v1/chat/rooms",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 1

    async def test_list_rooms_no_auth(self, client):
        r = await client.get("/api/v1/chat/rooms")
        assert r.status_code in (401, 403)


class TestChatMessages:
    async def _create_room(self, client, token, appt_id):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={appt_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()["id"]

    async def test_send_message(self, client, patient_token, confirmed_appointment):
        room_id = await self._create_room(client, patient_token, confirmed_appointment.id)
        r = await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "مرحبا دكتورة", "message_type": "text"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 201, r.text
        assert r.json()["content"] == "مرحبا دكتورة"
        assert r.json()["message_type"] == "text"

    async def test_send_empty_message_rejected(self, client, patient_token, confirmed_appointment):
        room_id = await self._create_room(client, patient_token, confirmed_appointment.id)
        r = await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "", "message_type": "text"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 422

    async def test_list_messages(self, client, patient_token, confirmed_appointment):
        room_id = await self._create_room(client, patient_token, confirmed_appointment.id)
        # Send 3 messages
        for i in range(3):
            await client.post(
                f"/api/v1/chat/rooms/{room_id}/messages",
                json={"content": f"رسالة {i}", "message_type": "text"},
                headers={"Authorization": f"Bearer {patient_token}"},
            )
        r = await client.get(
            f"/api/v1/chat/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 200
        assert r.json()["meta"]["total"] == 3

    async def test_doctor_can_send_and_read_messages(self, client, patient_token, doctor_token, confirmed_appointment):
        room_id = await self._create_room(client, patient_token, confirmed_appointment.id)

        # Patient sends
        await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "سؤال"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )

        # Doctor reads
        r = await client.get(
            f"/api/v1/chat/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r.status_code == 200
        assert r.json()["meta"]["total"] == 1

        # Doctor replies
        r2 = await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "إجابة"},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r2.status_code == 201

    async def test_unauthorized_user_cannot_access_room(self, client, admin_token, patient_token, confirmed_appointment):
        room_id = await self._create_room(client, patient_token, confirmed_appointment.id)
        r = await client.get(
            f"/api/v1/chat/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 403

    async def test_nonexistent_room(self, client, patient_token):
        r = await client.get(
            f"/api/v1/chat/rooms/{uuid.uuid4()}/messages",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r.status_code == 404


class TestReadReceipts:
    async def test_mark_read(self, client, patient_token, doctor_token, confirmed_appointment):
        # Create room and send messages
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        room_id = r.json()["id"]

        # Patient sends messages
        for i in range(3):
            await client.post(
                f"/api/v1/chat/rooms/{room_id}/messages",
                json={"content": f"msg {i}"},
                headers={"Authorization": f"Bearer {patient_token}"},
            )

        # Doctor marks read
        r2 = await client.patch(
            f"/api/v1/chat/rooms/{room_id}/read",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r2.status_code == 200
        assert "3" in r2.json()["message"]  # "3 messages marked as read"


class TestCloseRoom:
    async def test_doctor_can_close(self, client, patient_token, doctor_token, confirmed_appointment):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        room_id = r.json()["id"]

        r2 = await client.patch(
            f"/api/v1/chat/rooms/{room_id}/close",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "closed"

    async def test_patient_cannot_close(self, client, patient_token, confirmed_appointment):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        room_id = r.json()["id"]

        r2 = await client.patch(
            f"/api/v1/chat/rooms/{room_id}/close",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r2.status_code == 403

    async def test_send_to_closed_room_rejected(self, client, patient_token, doctor_token, confirmed_appointment):
        r = await client.post(
            f"/api/v1/chat/rooms?appointment_id={confirmed_appointment.id}",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        room_id = r.json()["id"]

        # Close
        await client.patch(
            f"/api/v1/chat/rooms/{room_id}/close",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        # Try to send
        r3 = await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "test"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert r3.status_code == 400
        assert r3.json()["detail"]["code"] == "ROOM_CLOSED"
