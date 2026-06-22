"""Device endpoints — FCM token registration."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.device import Device, DevicePlatform
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/devices", tags=["Devices"])


class DeviceRegisterRequest(BaseModel):
    fcm_token: str = Field(..., min_length=10, max_length=500)
    platform: str = Field("android", pattern="^(android|ios)$")
    device_name: str = Field(None, max_length=100)


@router.post("/register", status_code=201, response_model=MessageResponse)
async def register_device(
    body: DeviceRegisterRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or update a device for push notifications."""
    # Check if token already exists for this user
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.fcm_token == body.fcm_token,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.platform = DevicePlatform(body.platform)
        existing.device_name = body.device_name
        existing.is_active = True
    else:
        device = Device(
            user_id=current_user.id,
            fcm_token=body.fcm_token,
            platform=DevicePlatform(body.platform),
            device_name=body.device_name,
            is_active=True,
        )
        db.add(device)

    await db.commit()
    return MessageResponse(
        message="Device registered",
        message_ar="تم تسجيل الجهاز",
    )


@router.delete("/unregister", response_model=MessageResponse)
async def unregister_device(
    fcm_token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Unregister a device (e.g. on logout)."""
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.fcm_token == fcm_token,
        )
    )
    device = result.scalar_one_or_none()
    if device:
        device.is_active = False
        await db.commit()

    return MessageResponse(
        message="Device unregistered",
        message_ar="تم إلغاء تسجيل الجهاز",
    )
