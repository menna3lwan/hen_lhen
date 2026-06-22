"""Doctor endpoints."""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_doctor
from app.models.user import User
from app.services.doctor_service import DoctorService
from app.schemas.doctor import (
    DoctorListItemOut,
    DoctorProfileOut,
    DoctorUpdateRequest,
    DoctorOnlineStatusRequest,
    AvailabilityOut,
    TimeSlotOut,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.core.cache import cache, doctor_profile_key, doctor_online_key
from app.core.config import settings

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=PaginatedResponse)
async def list_doctors(
    specialty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, pattern="^(rating|fee|experience)$"),
    order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    online: Optional[bool] = Query(None),
    governorate: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List/search doctors with filtering, sorting, pagination."""
    service = DoctorService(db)
    doctors, total = await service.list_doctors(
        specialty=specialty, search=search, sort=sort,
        order=order or "desc", online=online, governorate=governorate,
        page=page, limit=limit,
    )
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=doctors,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.get("/{doctor_id}", response_model=DoctorProfileOut)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get doctor profile with branches (cached)."""
    # Try cache
    cached = await cache.get(doctor_profile_key(doctor_id))
    if cached:
        return DoctorProfileOut(**cached)

    service = DoctorService(db)
    profile = await service.get_doctor_profile(doctor_id)
    if not profile:
        raise HTTPException(status_code=404, detail={
            "code": "DOCTOR_NOT_FOUND",
            "message": "Doctor not found",
            "message_ar": "الدكتورة غير موجودة",
        })

    # Cache for 5 minutes
    await cache.set(doctor_profile_key(doctor_id), profile, ttl=settings.CACHE_TTL_DOCTOR_PROFILE)
    return DoctorProfileOut(**profile)


@router.get("/{doctor_id}/availability", response_model=AvailabilityOut)
async def get_availability(
    doctor_id: uuid.UUID,
    target_date: date = Query(..., alias="date"),
    branch_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get available time slots for a doctor on a date."""
    service = DoctorService(db)
    slots = await service.get_availability(doctor_id, target_date, branch_id)
    return AvailabilityOut(slots=[TimeSlotOut(**s) for s in slots])


@router.put("/profile", response_model=DoctorProfileOut)
async def update_profile(
    body: DoctorUpdateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Update current doctor's profile."""
    service = DoctorService(db)
    updated = await service.update_doctor_profile(
        current_user.id,
        body.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail={
            "code": "DOCTOR_NOT_FOUND", "message": "Doctor not found", "message_ar": "الدكتورة غير موجودة",
        })
    # Invalidate cached profile
    await cache.delete(doctor_profile_key(current_user.id))
    return DoctorProfileOut(**updated)


@router.put("/online-status")
async def set_online_status(
    body: DoctorOnlineStatusRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Set doctor online/offline status (cached in Redis)."""
    service = DoctorService(db)
    await service.set_online_status(current_user.id, body.is_online)

    # Cache online status separately (short TTL — 60s heartbeat)
    await cache.set(doctor_online_key(current_user.id), body.is_online, ttl=60)
    # Invalidate profile cache since is_online changed
    await cache.delete(doctor_profile_key(current_user.id))

    return {"is_online": body.is_online}
