"""Review endpoints."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.v1.deps import get_current_patient
from app.models.user import User
from app.models.review import Review
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(tags=["Reviews"])


class ReviewCreateRequest(BaseModel):
    appointment_id: uuid.UUID
    rating: float = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    rating: float
    comment: Optional[str] = None
    patient_name: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/reviews", response_model=ReviewOut, status_code=201, tags=["Reviews"])
async def create_review(
    body: ReviewCreateRequest,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Submit a review for a completed appointment."""
    appt = await db.get(Appointment, body.appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail={
            "code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found",
            "message_ar": "الموعد غير موجود",
        })
    if appt.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail={
            "code": "NOT_YOUR_APPOINTMENT", "message": "Not your appointment",
            "message_ar": "هذا ليس موعدك",
        })
    if appt.status != AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail={
            "code": "NOT_COMPLETED", "message": "Can only review completed appointments",
            "message_ar": "يمكن تقييم المواعيد المكتملة فقط",
        })

    # Check duplicate
    existing = await db.execute(
        select(Review).where(Review.appointment_id == body.appointment_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={
            "code": "ALREADY_REVIEWED", "message": "Already reviewed",
            "message_ar": "تم التقييم بالفعل",
        })

    review = Review(
        doctor_id=appt.doctor_id,
        patient_id=current_user.id,
        appointment_id=body.appointment_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)

    # Update doctor avg rating
    from app.models.user import Doctor
    doctor = await db.get(Doctor, appt.doctor_id)
    if doctor:
        doctor.reviews_count += 1
        # Recalculate average
        avg_result = await db.execute(
            select(func.avg(Review.rating)).where(Review.doctor_id == appt.doctor_id)
        )
        new_avg = avg_result.scalar() or body.rating
        doctor.rating = round(float(new_avg), 2)

    await db.flush()

    return ReviewOut(
        id=review.id,
        doctor_id=review.doctor_id,
        patient_id=review.patient_id,
        rating=float(review.rating),
        comment=review.comment,
        patient_name=current_user.name,
        created_at=review.created_at.isoformat(),
    )


@router.get("/doctors/{doctor_id}/reviews", response_model=PaginatedResponse, tags=["Reviews"])
async def list_doctor_reviews(
    doctor_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get reviews for a doctor."""
    count_q = select(func.count()).where(Review.doctor_id == doctor_id)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Review, User)
        .join(User, Review.patient_id == User.id)
        .where(Review.doctor_id == doctor_id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "id": str(review.id),
            "doctor_id": str(review.doctor_id),
            "patient_id": str(review.patient_id),
            "rating": float(review.rating),
            "comment": review.comment,
            "patient_name": user.name,
            "created_at": review.created_at.isoformat(),
        }
        for review, user in rows
    ]

    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )
