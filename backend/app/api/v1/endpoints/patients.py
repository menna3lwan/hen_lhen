"""Patient endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_patient
from app.models.user import User, Patient
from app.schemas.patient import PatientProfileOut, PatientUpdateRequest

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/profile", response_model=PatientProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get current patient's profile."""
    patient = await db.get(Patient, current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail={
            "code": "PATIENT_NOT_FOUND", "message": "Patient profile not found",
            "message_ar": "الملف الشخصي غير موجود",
        })
    return PatientProfileOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        governorate=patient.governorate,
        blood_type=patient.blood_type,
        date_of_birth=str(patient.date_of_birth) if patient.date_of_birth else None,
        is_verified=current_user.is_verified,
        language=current_user.language,
    )


@router.put("/profile", response_model=PatientProfileOut)
async def update_profile(
    body: PatientUpdateRequest,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Update current patient's profile."""
    patient = await db.get(Patient, current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail={
            "code": "PATIENT_NOT_FOUND", "message": "Patient profile not found",
            "message_ar": "الملف الشخصي غير موجود",
        })

    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        current_user.name = data["name"]
    if "phone" in data:
        current_user.phone = data["phone"]
    if "governorate" in data:
        patient.governorate = data["governorate"]
    if "blood_type" in data:
        patient.blood_type = data["blood_type"]

    await db.flush()

    return PatientProfileOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        governorate=patient.governorate,
        blood_type=patient.blood_type,
        date_of_birth=str(patient.date_of_birth) if patient.date_of_birth else None,
        is_verified=current_user.is_verified,
        language=current_user.language,
    )
