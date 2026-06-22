"""Medical Record schemas."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PrescriptionItem(BaseModel):
    medication: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = None


class MedicalRecordCreateRequest(BaseModel):
    appointment_id: UUID
    type: str = Field("consultation", pattern="^(consultation|prescription|lab_result|diagnosis|follow_up)$")
    diagnosis: Optional[str] = Field(None, max_length=5000)
    notes: Optional[str] = Field(None, max_length=5000)
    prescriptions: Optional[List[PrescriptionItem]] = None
    attachments: Optional[List[str]] = None  # list of file URLs
    is_private: bool = False
    follow_up_date: Optional[datetime] = None


class MedicalRecordUpdateRequest(BaseModel):
    diagnosis: Optional[str] = Field(None, max_length=5000)
    notes: Optional[str] = Field(None, max_length=5000)
    prescriptions: Optional[List[PrescriptionItem]] = None
    attachments: Optional[List[str]] = None
    follow_up_date: Optional[datetime] = None


class MedicalRecordOut(BaseModel):
    id: UUID
    appointment_id: UUID
    patient_id: UUID
    doctor_id: UUID
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    type: str
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    prescriptions: Optional[list] = None
    attachments: Optional[list] = None
    is_private: bool = False
    follow_up_date: Optional[str] = None
    created_at: str
    updated_at: str
