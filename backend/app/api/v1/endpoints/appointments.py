"""Appointment endpoints."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user, get_current_patient, get_current_doctor, get_current_admin
from app.models.user import User, UserRole
from app.services.appointment_service import AppointmentService
from app.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentStatusUpdateRequest,
    AppointmentCancelRequest,
    AppointmentOut,
)
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/appointments", tags=["Appointments"])

ERROR_MAP = {
    "DOCTOR_NOT_FOUND": (404, "Doctor not found", "الدكتورة غير موجودة"),
    "DOCTOR_NOT_APPROVED": (400, "Doctor not approved yet", "الدكتورة غير معتمدة بعد"),
    "SLOT_UNAVAILABLE": (409, "This time slot is already booked", "هذا الموعد محجوز بالفعل"),
    "APPOINTMENT_NOT_FOUND": (404, "Appointment not found", "الموعد غير موجود"),
    "NOT_YOUR_APPOINTMENT": (403, "This is not your appointment", "هذا ليس موعدك"),
    "INVALID_STATUS_TRANSITION": (400, "Invalid status change", "تغيير حالة غير صالح"),
    "CANNOT_CANCEL": (400, "Cannot cancel this appointment", "لا يمكن إلغاء هذا الموعد"),
}


def _raise(code: str):
    sc, msg, msg_ar = ERROR_MAP.get(code, (400, code, code))
    raise HTTPException(status_code=sc, detail={"code": code, "message": msg, "message_ar": msg_ar})


@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    body: AppointmentCreateRequest,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Book a new appointment (patient only)."""
    service = AppointmentService(db)
    try:
        result = await service.create_appointment(
            patient_id=current_user.id,
            doctor_id=body.doctor_id,
            appt_date=body.date,
            appt_time_str=body.time,
            appt_type=body.type,
            branch_id=body.branch_id,
            promo_code_str=body.promo_code,
        )
    except ValueError as e:
        _raise(str(e))
    return AppointmentOut(**result)


@router.get("", response_model=PaginatedResponse)
async def list_appointments(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List appointments for the current user (patient or doctor)."""
    service = AppointmentService(db)
    data, total = await service.list_appointments(
        user_id=current_user.id,
        role=current_user.role,
        status_filter=status_filter,
        page=page, limit=limit,
    )
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.get("/{appt_id}", response_model=AppointmentOut)
async def get_appointment(
    appt_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get appointment details."""
    service = AppointmentService(db)
    result = await service.get_appointment(appt_id)
    if not result:
        _raise("APPOINTMENT_NOT_FOUND")
    # Ensure user owns the appointment
    if result["patient_id"] != current_user.id and result["doctor_id"] != current_user.id:
        _raise("NOT_YOUR_APPOINTMENT")
    return AppointmentOut(**result)


@router.patch("/{appt_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appt_id: uuid.UUID,
    body: AppointmentStatusUpdateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Doctor: confirm, complete, or cancel appointment."""
    service = AppointmentService(db)
    try:
        result = await service.update_status_by_doctor(
            appt_id, current_user.id, body.status, body.reason,
        )
    except ValueError as e:
        _raise(str(e))
    return AppointmentOut(**result)


@router.patch("/{appt_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appt_id: uuid.UUID,
    body: AppointmentCancelRequest,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Patient: cancel appointment."""
    service = AppointmentService(db)
    try:
        result = await service.cancel_by_patient(
            appt_id, current_user.id, body.reason,
        )
    except ValueError as e:
        _raise(str(e))
    return AppointmentOut(**result)


@router.post("/send-reminders")
async def trigger_reminders(
    hours: int = Query(24, ge=1, le=72),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger appointment reminders for upcoming appointments (admin/cron)."""
    from app.services.reminder_service import send_appointment_reminders
    sent = await send_appointment_reminders(db, hours_before=hours)
    await db.commit()
    return {
        "message": f"Sent {sent} reminders",
        "message_ar": f"تم إرسال {sent} تذكير",
        "count": sent,
    }
