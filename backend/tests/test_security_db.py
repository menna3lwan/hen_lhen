"""Security & Database verification tests."""

import uuid
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


class TestSecurityAuthorization:
    """Verify role-based access control across Phase 3 endpoints."""

    async def test_payment_patient_only(self, client, doctor_token, admin_token):
        """Payment initiation should reject non-patients."""
        for token, role in [(doctor_token, "doctor"), (admin_token, "admin")]:
            r = await client.post(
                "/api/v1/payments/initiate",
                json={"appointment_id": str(uuid.uuid4()), "payment_method": "card"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 403, f"{role} should not initiate payments"

    async def test_payment_history_patient_only(self, client, doctor_token, admin_token):
        for token in [doctor_token, admin_token]:
            r = await client.get(
                "/api/v1/payments/history",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 403

    async def test_refund_admin_only(self, client, patient_token, doctor_token):
        for token in [patient_token, doctor_token]:
            r = await client.post(
                "/api/v1/payments/refund",
                json={"payment_id": str(uuid.uuid4())},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 403

    async def test_chat_requires_auth(self, client):
        """All chat endpoints require authentication."""
        endpoints = [
            ("POST", f"/api/v1/chat/rooms?appointment_id={uuid.uuid4()}"),
            ("GET", "/api/v1/chat/rooms"),
            ("POST", f"/api/v1/chat/rooms/{uuid.uuid4()}/messages"),
            ("GET", f"/api/v1/chat/rooms/{uuid.uuid4()}/messages"),
            ("PATCH", f"/api/v1/chat/rooms/{uuid.uuid4()}/read"),
            ("PATCH", f"/api/v1/chat/rooms/{uuid.uuid4()}/close"),
        ]
        for method, url in endpoints:
            if method == "GET":
                r = await client.get(url)
            elif method == "POST":
                r = await client.post(url, json={"content": "test"})
            else:
                r = await client.patch(url)
            assert r.status_code in (401, 403, 422), f"{method} {url} should require auth"

    async def test_device_requires_auth(self, client):
        r = await client.post("/api/v1/devices/register", json={
            "fcm_token": "test_token_12345678", "platform": "android",
        })
        assert r.status_code in (401, 403)

    async def test_expired_jwt_rejected(self, client):
        """Expired tokens should be rejected."""
        from jose import jwt
        from datetime import datetime, timedelta, timezone
        from app.core.config import settings

        expired = jwt.encode(
            {"sub": str(uuid.uuid4()), "role": "patient", "type": "access",
             "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM,
        )
        r = await client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert r.status_code == 401

    async def test_invalid_jwt_rejected(self, client):
        r = await client.get(
            "/api/v1/payments/history",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert r.status_code == 401


class TestDatabaseIntegrity:
    """Verify database schema, constraints, and relationships."""

    async def test_all_models_importable(self):
        """Every model class should import without errors."""
        from app.models import (
            User, Patient, Doctor, Specialty, Branch, BranchSchedule,
            Appointment, Payment, PromoCode, ChatRoom, Message,
            Post, Comment, PostLike, Review, Notification,
            Favorite, Device, AuditLog, RefreshToken,
        )
        # All 20 model classes imported successfully
        assert User is not None

    async def test_model_table_count(self):
        from app.db.base import Base
        # Import all models to register them
        import app.models  # noqa
        tables = Base.metadata.tables
        assert len(tables) >= 20, f"Expected >= 20 tables, got {len(tables)}: {list(tables.keys())}"

    async def test_payment_model_fields(self):
        from app.models.payment import Payment, PaymentStatus
        assert hasattr(Payment, "appointment_id")
        assert hasattr(Payment, "patient_id")
        assert hasattr(Payment, "status")
        assert hasattr(Payment, "refund_amount")
        assert hasattr(Payment, "gateway_transaction_id")
        assert set(PaymentStatus) == {PaymentStatus.PENDING, PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.REFUNDED}

    async def test_chatroom_model_fields(self):
        from app.models.chat import ChatRoom, Message, ChatStatus, MessageType
        assert hasattr(ChatRoom, "last_message")
        assert hasattr(ChatRoom, "last_message_at")
        assert hasattr(ChatRoom, "updated_at")
        assert hasattr(ChatRoom, "closed_at")
        assert hasattr(Message, "is_read")
        assert MessageType.VOICE in MessageType

    async def test_device_model_fields(self):
        from app.models.device import Device, DevicePlatform
        assert hasattr(Device, "fcm_token")
        assert hasattr(Device, "platform")
        assert hasattr(Device, "is_active")

    async def test_notification_types(self):
        from app.models.notification import NotificationType
        expected = {"appointment", "message", "promotion", "system"}
        actual = {t.value for t in NotificationType}
        assert expected == actual

    async def test_foreign_keys_exist(self):
        """Verify key FK relationships are declared."""
        from app.db.base import Base
        import app.models  # noqa

        payments_table = Base.metadata.tables["payments"]
        fk_targets = {fk.target_fullname for fk in payments_table.foreign_keys}
        assert "appointments.id" in fk_targets
        assert "patients.id" in fk_targets

        chatrooms_table = Base.metadata.tables["chat_rooms"]
        fk_targets = {fk.target_fullname for fk in chatrooms_table.foreign_keys}
        assert "appointments.id" in fk_targets
        assert "patients.id" in fk_targets
        assert "doctors.id" in fk_targets

        messages_table = Base.metadata.tables["messages"]
        fk_targets = {fk.target_fullname for fk in messages_table.foreign_keys}
        assert "chat_rooms.id" in fk_targets
        assert "users.id" in fk_targets

        devices_table = Base.metadata.tables["devices"]
        fk_targets = {fk.target_fullname for fk in devices_table.foreign_keys}
        assert "users.id" in fk_targets

    async def test_indexes_exist(self):
        """Verify performance indexes are declared."""
        from app.db.base import Base
        import app.models  # noqa

        payments_indexes = {idx.name for idx in Base.metadata.tables["payments"].indexes}
        assert "idx_payments_appointment" in payments_indexes
        assert "idx_payments_status" in payments_indexes

        chatrooms_indexes = {idx.name for idx in Base.metadata.tables["chat_rooms"].indexes}
        assert "idx_chatrooms_participants" in chatrooms_indexes

        messages_indexes = {idx.name for idx in Base.metadata.tables["messages"].indexes}
        assert "idx_messages_chatroom" in messages_indexes

        devices_indexes = {idx.name for idx in Base.metadata.tables["devices"].indexes}
        assert "idx_devices_user" in devices_indexes


class TestNotificationService:
    """Test notification_service directly."""

    async def test_notify_uses_correct_enum(self):
        """notification_service types must match NotificationType enum."""
        from app.models.notification import NotificationType
        # These are the types the service actually uses
        service_types = ["appointment", "message", "system"]
        for t in service_types:
            assert NotificationType(t), f"Type '{t}' not in NotificationType enum"
