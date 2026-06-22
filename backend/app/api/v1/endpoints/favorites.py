"""Favorites endpoints (patient only)."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_patient
from app.models.user import User, Doctor
from app.models.specialty import Specialty
from app.models.favorite import Favorite
from app.schemas.doctor import DoctorListItemOut
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=List[DoctorListItemOut])
async def list_favorites(
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """List patient's favorite doctors."""
    result = await db.execute(
        select(Doctor, User, Specialty, Favorite)
        .join(User, Doctor.id == User.id)
        .join(Specialty, Doctor.specialty_id == Specialty.id)
        .join(Favorite, Favorite.doctor_id == Doctor.id)
        .where(Favorite.patient_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    rows = result.all()

    return [
        DoctorListItemOut(
            id=user.id,
            name=user.name,
            avatar_url=user.avatar_url,
            specialty_name_ar=spec.name_ar,
            specialty_name_en=spec.name_en,
            consultation_fee=float(doctor.consultation_fee),
            rating=float(doctor.rating),
            reviews_count=doctor.reviews_count,
            experience_years=doctor.experience_years,
            patients_count=doctor.patients_count,
            is_online=doctor.is_online,
            is_verified=user.is_verified,
        )
        for doctor, user, spec, fav in rows
    ]


@router.post("/{doctor_id}", status_code=201)
async def add_favorite(
    doctor_id: uuid.UUID,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Add doctor to favorites."""
    # Check doctor exists
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail={
            "code": "DOCTOR_NOT_FOUND", "message": "Doctor not found",
            "message_ar": "الدكتورة غير موجودة",
        })

    # Check already favorited
    existing = await db.execute(
        select(Favorite).where(
            Favorite.patient_id == current_user.id,
            Favorite.doctor_id == doctor_id,
        )
    )
    if existing.scalar_one_or_none():
        return MessageResponse(message="Already in favorites", message_ar="موجودة بالفعل في المفضلة")

    fav = Favorite(patient_id=current_user.id, doctor_id=doctor_id)
    db.add(fav)
    await db.flush()
    return MessageResponse(message="Added to favorites", message_ar="تمت الإضافة للمفضلة")


@router.delete("/{doctor_id}", response_model=MessageResponse)
async def remove_favorite(
    doctor_id: uuid.UUID,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Remove doctor from favorites."""
    result = await db.execute(
        select(Favorite).where(
            Favorite.patient_id == current_user.id,
            Favorite.doctor_id == doctor_id,
        )
    )
    fav = result.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.flush()
    return MessageResponse(message="Removed from favorites", message_ar="تمت الإزالة من المفضلة")
