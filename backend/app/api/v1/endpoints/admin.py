"""Admin endpoints — doctor verification, promo codes, stats."""

import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User, Doctor, Patient, UserRole, VerificationStatus
from app.models.specialty import Specialty
from app.models.appointment import Appointment
from app.models.payment import Payment
from app.models.promo_code import PromoCode, PromoType
from app.schemas.auth import MessageResponse
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Schemas ──

class VerifyDoctorRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    reason: Optional[str] = None


class PromoCodeCreateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    type: str = Field(..., pattern="^(percentage|fixed)$")
    value: float = Field(..., gt=0)
    max_uses: Optional[int] = Field(None, ge=1)
    min_amount: float = Field(0, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True


# ── Doctor Verification ──

@router.get("/doctors/pending", response_model=PaginatedResponse)
async def list_pending_doctors(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List doctors awaiting verification."""
    base = (
        select(Doctor, User, Specialty)
        .join(User, Doctor.id == User.id)
        .join(Specialty, Doctor.specialty_id == Specialty.id)
        .where(Doctor.verification_status == VerificationStatus.PENDING)
    )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = base.order_by(User.created_at.asc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "specialty_ar": spec.name_ar,
            "specialty_en": spec.name_en,
            "license_number": doctor.license_number,
            "experience_years": doctor.experience_years,
            "bio": doctor.bio,
            "created_at": user.created_at.isoformat(),
        }
        for doctor, user, spec in rows
    ]

    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.patch("/doctors/{doctor_id}/verify", response_model=MessageResponse)
async def verify_doctor(
    doctor_id: uuid.UUID,
    body: VerifyDoctorRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a doctor registration."""
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail={
            "code": "DOCTOR_NOT_FOUND", "message": "Doctor not found",
            "message_ar": "الدكتورة غير موجودة",
        })

    if doctor.verification_status != VerificationStatus.PENDING:
        raise HTTPException(status_code=400, detail={
            "code": "NOT_PENDING", "message": "Doctor is not in pending state",
            "message_ar": "الدكتورة ليست في حالة انتظار",
        })

    doctor.verification_status = VerificationStatus(body.status)
    doctor.verified_at = datetime.now(timezone.utc)
    doctor.verified_by = current_user.id

    if body.status == "approved":
        user = await db.get(User, doctor_id)
        if user:
            user.is_verified = True

    await db.flush()

    status_ar = "تمت الموافقة" if body.status == "approved" else "تم الرفض"
    return MessageResponse(
        message=f"Doctor {body.status}",
        message_ar=f"{status_ar} على طلب الدكتورة",
    )


# ── Promo Codes ──

@router.post("/promo-codes", status_code=201)
async def create_promo_code(
    body: PromoCodeCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new promo code."""
    # Check duplicate
    existing = await db.execute(
        select(PromoCode).where(PromoCode.code == body.code.upper().strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={
            "code": "CODE_EXISTS", "message": "Promo code already exists",
            "message_ar": "كود الخصم موجود بالفعل",
        })

    promo = PromoCode(
        code=body.code.upper().strip(),
        type=PromoType(body.type),
        value=body.value,
        max_uses=body.max_uses,
        min_amount=body.min_amount,
        max_discount=body.max_discount,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        is_active=body.is_active,
    )
    db.add(promo)
    await db.flush()

    return {
        "id": str(promo.id),
        "code": promo.code,
        "type": promo.type.value,
        "value": float(promo.value),
        "is_active": promo.is_active,
    }


@router.get("/promo-codes")
async def list_promo_codes(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all promo codes."""
    result = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    codes = result.scalars().all()
    return {
        "data": [
            {
                "id": str(c.id),
                "code": c.code,
                "type": c.type.value,
                "value": float(c.value),
                "max_uses": c.max_uses,
                "current_uses": c.current_uses,
                "is_active": c.is_active,
                "valid_from": c.valid_from.isoformat(),
                "valid_until": c.valid_until.isoformat(),
            }
            for c in codes
        ]
    }


# ── Reports / Stats ──

@router.get("/reports/users")
async def user_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get user statistics."""
    total_patients = (await db.execute(
        select(func.count()).where(User.role == UserRole.PATIENT, User.deleted_at == None)
    )).scalar() or 0

    total_doctors = (await db.execute(
        select(func.count()).where(User.role == UserRole.DOCTOR, User.deleted_at == None)
    )).scalar() or 0

    approved_doctors = (await db.execute(
        select(func.count()).where(
            Doctor.verification_status == VerificationStatus.APPROVED
        )
    )).scalar() or 0

    pending_doctors = (await db.execute(
        select(func.count()).where(
            Doctor.verification_status == VerificationStatus.PENDING
        )
    )).scalar() or 0

    total_appointments = (await db.execute(
        select(func.count(Appointment.id))
    )).scalar() or 0

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "approved_doctors": approved_doctors,
        "pending_doctors": pending_doctors,
        "total_appointments": total_appointments,
    }
