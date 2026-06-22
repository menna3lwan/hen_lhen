"""Appointment schemas."""

from typing import Optional, List
from uuid import UUID
from datetime import date, time
from pydantic import BaseModel, Field


class AppointmentCreateRequest(BaseModel):
    doctor_id: UUID
    branch_id: Optional[UUID] = None
    date: date
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    type: str = Field(..., pattern="^(online|clinic)$")
    promo_code: Optional[str] = None


class AppointmentStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(confirmed|cancelled|completed)$")
    reason: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    reason: Optional[str] = None


class AppointmentDoctorOut(BaseModel):
    id: UUID
    name: str
    avatar_url: Optional[str] = None
    specialty_name_ar: Optional[str] = None
    specialty_name_en: Optional[str] = None

    model_config = {"from_attributes": True}


class AppointmentPatientOut(BaseModel):
    id: UUID
    name: str
    phone: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class AppointmentOut(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    branch_id: Optional[UUID] = None
    date: str
    time: str
    type: str
    status: str
    amount: float
    discount_amount: float = 0
    notes: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    created_at: str
    doctor: Optional[AppointmentDoctorOut] = None
    patient: Optional[AppointmentPatientOut] = None

    model_config = {"from_attributes": True}
