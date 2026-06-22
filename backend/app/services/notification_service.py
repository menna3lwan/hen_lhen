"""Notification service — create notifications + FCM push (placeholder).

Usage from other services:
    from app.services.notification_service import notify
    await notify(db, user_id=..., type="appointment_confirmed", title_ar="...", body_ar="...", data={...})
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.device import Device


async def notify(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: str,
    title_ar: str,
    body_ar: str,
    title_en: Optional[str] = None,
    body_en: Optional[str] = None,
    data: Optional[dict] = None,
):
    """Create a notification and attempt push delivery.

    Args:
        db: Database session
        user_id: Target user
        type: NotificationType value (appointment_confirmed, new_message, etc.)
        title_ar: Arabic title (primary)
        body_ar: Arabic body
        title_en: English title (optional)
        body_en: English body (optional)
        data: Extra JSONB payload (appointment_id, room_id, etc.)
    """
    # 1. Store in DB
    notification = Notification(
        user_id=user_id,
        type=NotificationType(type),
        title=title_ar,
        body=body_ar,
        data=data or {},
    )
    db.add(notification)
    await db.flush()

    # 2. Push via FCM (placeholder — replace with firebase_admin in production)
    await _send_push(db, user_id, title_ar, body_ar, data)

    return notification


async def notify_many(
    db: AsyncSession,
    user_ids: List[uuid.UUID],
    type: str,
    title_ar: str,
    body_ar: str,
    data: Optional[dict] = None,
):
    """Send the same notification to multiple users."""
    for uid in user_ids:
        await notify(db, uid, type, title_ar, body_ar, data=data)


async def _send_push(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
    data: Optional[dict] = None,
):
    """Send push notification via FCM.

    TODO: Replace with actual firebase_admin implementation:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=device.fcm_token,
        )
        messaging.send(message)
    """
    # Get active devices for user
    result = await db.execute(
        select(Device).where(
            Device.user_id == user_id,
            Device.is_active == True,
        )
    )
    devices = result.scalars().all()

    for device in devices:
        # In production: send via firebase_admin.messaging
        # For now, log the intent
        pass  # FCM push placeholder


# ── Convenience helpers for common notification types ──

async def notify_appointment_confirmed(
    db: AsyncSession, patient_id: uuid.UUID, doctor_name: str, appointment_id: uuid.UUID,
):
    await notify(
        db, patient_id,
        type="appointment",
        title_ar="تأكيد الموعد",
        body_ar=f"تم تأكيد موعدك مع د. {doctor_name}",
        data={"appointment_id": str(appointment_id), "action": "confirmed"},
    )


async def notify_appointment_cancelled(
    db: AsyncSession, patient_id: uuid.UUID, doctor_name: str, appointment_id: uuid.UUID,
):
    await notify(
        db, patient_id,
        type="appointment",
        title_ar="إلغاء الموعد",
        body_ar=f"تم إلغاء موعدك مع د. {doctor_name}",
        data={"appointment_id": str(appointment_id), "action": "cancelled"},
    )


async def notify_new_message(
    db: AsyncSession, recipient_id: uuid.UUID, sender_name: str, room_id: uuid.UUID,
):
    await notify(
        db, recipient_id,
        type="message",
        title_ar="رسالة جديدة",
        body_ar=f"رسالة جديدة من {sender_name}",
        data={"chat_room_id": str(room_id)},
    )


async def notify_new_appointment(
    db: AsyncSession, doctor_id: uuid.UUID, patient_name: str, appointment_id: uuid.UUID,
):
    await notify(
        db, doctor_id,
        type="appointment",
        title_ar="حجز جديد",
        body_ar=f"لديك حجز جديد من {patient_name}",
        data={"appointment_id": str(appointment_id), "action": "new"},
    )


async def notify_payment_received(
    db: AsyncSession, doctor_id: uuid.UUID, amount: float, appointment_id: uuid.UUID,
):
    await notify(
        db, doctor_id,
        type="appointment",
        title_ar="دفعة جديدة",
        body_ar=f"تم استلام دفعة بقيمة {amount} ج.م",
        data={"appointment_id": str(appointment_id), "action": "payment_received"},
    )
