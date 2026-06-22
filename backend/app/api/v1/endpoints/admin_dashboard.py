"""Admin Dashboard endpoints — analytics, revenue, reports, audit logs."""

import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User, Doctor, Patient, UserRole, VerificationStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.payment import Payment, PaymentStatus
from app.models.review import Review
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.audit_service import list_audit_logs

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get("/overview")
async def dashboard_overview(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """High-level dashboard overview."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Users
    total_patients = (await db.execute(
        select(func.count()).where(User.role == UserRole.PATIENT, User.deleted_at == None)
    )).scalar() or 0

    total_doctors = (await db.execute(
        select(func.count()).where(User.role == UserRole.DOCTOR, User.deleted_at == None)
    )).scalar() or 0

    new_patients_30d = (await db.execute(
        select(func.count()).where(
            User.role == UserRole.PATIENT, User.created_at >= thirty_days_ago
        )
    )).scalar() or 0

    pending_doctors = (await db.execute(
        select(func.count()).where(Doctor.verification_status == VerificationStatus.PENDING)
    )).scalar() or 0

    # Appointments
    total_appointments = (await db.execute(
        select(func.count(Appointment.id))
    )).scalar() or 0

    appointments_7d = (await db.execute(
        select(func.count(Appointment.id)).where(Appointment.created_at >= seven_days_ago)
    )).scalar() or 0

    completed_appointments = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.status == AppointmentStatus.COMPLETED
        )
    )).scalar() or 0

    cancelled_appointments = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.status == AppointmentStatus.CANCELLED
        )
    )).scalar() or 0

    # Revenue
    total_revenue = (await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.COMPLETED)
    )).scalar() or 0

    revenue_30d = (await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= thirty_days_ago,
        )
    )).scalar() or 0

    total_refunds = (await db.execute(
        select(func.sum(Payment.refund_amount)).where(Payment.status == PaymentStatus.REFUNDED)
    )).scalar() or 0

    return {
        "users": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "new_patients_30d": new_patients_30d,
            "pending_doctors": pending_doctors,
        },
        "appointments": {
            "total": total_appointments,
            "last_7_days": appointments_7d,
            "completed": completed_appointments,
            "cancelled": cancelled_appointments,
            "completion_rate": round(
                completed_appointments / total_appointments * 100, 1
            ) if total_appointments else 0,
        },
        "revenue": {
            "total": float(total_revenue),
            "last_30_days": float(revenue_30d),
            "total_refunds": float(total_refunds),
            "net_revenue": float(total_revenue) - float(total_refunds),
        },
    }


@router.get("/revenue")
async def revenue_report(
    period: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revenue breakdown by period."""
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=months * 30)

    if period == "daily":
        date_expr = func.date(Payment.paid_at)
    elif period == "weekly":
        date_expr = func.date_trunc("week", Payment.paid_at)
    else:
        date_expr = func.date_trunc("month", Payment.paid_at)

    result = await db.execute(
        select(
            date_expr.label("period"),
            func.count(Payment.id).label("count"),
            func.sum(Payment.amount).label("revenue"),
        )
        .where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= start_date,
        )
        .group_by(date_expr)
        .order_by(date_expr)
    )
    rows = result.all()

    return {
        "period": period,
        "data": [
            {
                "period": str(row.period),
                "count": row.count,
                "revenue": float(row.revenue) if row.revenue else 0,
            }
            for row in rows
        ],
    }


@router.get("/top-doctors")
async def top_doctors(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Top doctors by completed appointments and rating."""
    result = await db.execute(
        select(
            Doctor.id,
            User.name,
            Doctor.rating,
            Doctor.reviews_count,
            func.count(Appointment.id).label("appointment_count"),
        )
        .join(User, Doctor.id == User.id)
        .outerjoin(
            Appointment,
            (Appointment.doctor_id == Doctor.id) & (Appointment.status == AppointmentStatus.COMPLETED),
        )
        .where(Doctor.verification_status == VerificationStatus.APPROVED)
        .group_by(Doctor.id, User.name, Doctor.rating, Doctor.reviews_count)
        .order_by(func.count(Appointment.id).desc())
        .limit(limit)
    )
    rows = result.all()

    return {
        "data": [
            {
                "id": str(row.id),
                "name": row.name,
                "rating": float(row.rating),
                "reviews_count": row.reviews_count,
                "appointment_count": row.appointment_count,
            }
            for row in rows
        ]
    }


@router.get("/appointment-stats")
async def appointment_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Appointment statistics by status and date."""
    start = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Appointment.created_at).label("date"),
            Appointment.status,
            func.count(Appointment.id).label("count"),
        )
        .where(Appointment.created_at >= start)
        .group_by(func.date(Appointment.created_at), Appointment.status)
        .order_by(func.date(Appointment.created_at))
    )
    rows = result.all()

    # Group by date
    by_date = {}
    for row in rows:
        d = str(row.date)
        if d not in by_date:
            by_date[d] = {"date": d, "pending": 0, "confirmed": 0, "completed": 0, "cancelled": 0}
        by_date[d][row.status.value] = row.count

    return {"days": days, "data": list(by_date.values())}


@router.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Query audit logs (admin only)."""
    data, total = await list_audit_logs(
        db, entity_type=entity_type, action=action, page=page, limit=limit,
    )
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )
