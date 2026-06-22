"""Notification endpoints."""

import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user, get_current_admin
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.auth import MessageResponse
from app.services.notification_service import notify

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for current user."""
    base = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        base = base.where(Notification.is_read == False)

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Unread count (always returned)
    unread_q = select(func.count()).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    )
    unread_count = (await db.execute(unread_q)).scalar() or 0

    # Fetch
    query = base.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    notifs = result.scalars().all()

    data = [
        {
            "id": str(n.id),
            "title": n.title,
            "body": n.body,
            "type": n.type.value,
            "data": n.data,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifs
    ]

    pages = (total + limit - 1) // limit if limit else 1
    return {
        "data": data,
        "meta": {"total": total, "page": page, "limit": limit, "pages": pages},
        "unread_count": unread_count,
    }


@router.patch("/{notification_id}/read", response_model=MessageResponse)
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notif = await db.get(Notification, notification_id)
    if notif and notif.user_id == current_user.id:
        notif.is_read = True
        await db.flush()
    return MessageResponse(message="Marked as read", message_ar="تم التحديد كمقروء")


@router.patch("/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
    return MessageResponse(message="All marked as read", message_ar="تم تحديد الكل كمقروء")


# ── Batch / Admin Notifications ──

class BatchNotificationRequest(BaseModel):
    title: str = Field(..., max_length=200)
    body: str = Field(..., max_length=1000)
    target: str = Field(..., pattern="^(all|patients|doctors)$")


@router.post("/batch", status_code=201)
async def send_batch_notification(
    body: BatchNotificationRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Send a notification to all users of a target group (admin only)."""
    # Determine target roles
    if body.target == "patients":
        roles = [UserRole.PATIENT]
    elif body.target == "doctors":
        roles = [UserRole.DOCTOR]
    else:
        roles = [UserRole.PATIENT, UserRole.DOCTOR]

    # Get target user IDs
    result = await db.execute(
        select(User.id).where(
            User.role.in_(roles),
            User.is_active == True,
            User.deleted_at == None,
        )
    )
    user_ids = [row[0] for row in result.all()]

    # Send notifications
    sent = 0
    for uid in user_ids:
        await notify(
            db,
            user_id=uid,
            title=body.title,
            body=body.body,
            notification_type="system",
        )
        sent += 1

    await db.flush()
    return {
        "message": f"Sent {sent} notifications",
        "message_ar": f"تم إرسال {sent} إشعار",
        "count": sent,
    }
