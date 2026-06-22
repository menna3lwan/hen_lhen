"""Medical Records endpoints — create, read, list, update."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user, get_current_doctor
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordCreateRequest,
    MedicalRecordUpdateRequest,
    MedicalRecordOut,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])

ERROR_MAP = {
    "APPOINTMENT_NOT_FOUND": (404, "Appointment not found", "الموعد غير موجود"),
    "NOT_YOUR_APPOINTMENT": (403, "Not your appointment", "هذا ليس موعدك"),
    "APPOINTMENT_NOT_COMPLETED": (400, "Appointment not completed", "الموعد لم يكتمل بعد"),
    "RECORD_ALREADY_EXISTS": (409, "Record already exists for this type", "يوجد سجل بالفعل من هذا النوع"),
    "RECORD_NOT_FOUND": (404, "Record not found", "السجل غير موجود"),
    "NOT_YOUR_RECORD": (403, "Not your record", "هذا ليس سجلك"),
    "NOT_YOUR_RECORDS": (403, "Not your records", "هذه ليست سجلاتك"),
}


def _raise(code: str):
    status, msg, msg_ar = ERROR_MAP[code]
    raise HTTPException(status_code=status, detail={
        "code": code, "message": msg, "message_ar": msg_ar,
    })


@router.post("", status_code=201)
async def create_record(
    body: MedicalRecordCreateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Create a medical record (doctor only)."""
    svc = MedicalRecordService(db)
    try:
        result = await svc.create_record(
            doctor_id=current_user.id,
            appointment_id=body.appointment_id,
            record_type=body.type,
            diagnosis=body.diagnosis,
            notes=body.notes,
            prescriptions=body.prescriptions,
            attachments=body.attachments,
            is_private=body.is_private,
            follow_up_date=body.follow_up_date,
        )
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return result


@router.get("/{record_id}")
async def get_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single medical record."""
    svc = MedicalRecordService(db)
    try:
        result = await svc.get_record(record_id, current_user.id, current_user.role)
    except ValueError as e:
        _raise(str(e))
    return result


@router.get("/patient/{patient_id}", response_model=PaginatedResponse)
async def list_patient_records(
    patient_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List medical records for a patient."""
    svc = MedicalRecordService(db)
    try:
        data, total = await svc.list_patient_records(
            patient_id=patient_id,
            viewer_id=current_user.id,
            viewer_role=current_user.role,
            page=page, limit=limit,
            record_type=record_type,
        )
    except ValueError as e:
        _raise(str(e))
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.get("/appointment/{appointment_id}")
async def list_by_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all records for a specific appointment."""
    svc = MedicalRecordService(db)
    try:
        data = await svc.list_by_appointment(appointment_id, current_user.id)
    except ValueError as e:
        _raise(str(e))
    return {"data": data}


@router.put("/{record_id}")
async def update_record(
    record_id: uuid.UUID,
    body: MedicalRecordUpdateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Update a medical record (doctor who created it only)."""
    svc = MedicalRecordService(db)
    try:
        result = await svc.update_record(
            record_id=record_id,
            doctor_id=current_user.id,
            diagnosis=body.diagnosis,
            notes=body.notes,
            prescriptions=body.prescriptions,
            attachments=body.attachments,
            follow_up_date=body.follow_up_date,
        )
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return result
