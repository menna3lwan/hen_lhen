"""Patient schemas."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PatientProfileOut(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    avatar_url: Optional[str] = None
    governorate: str
    blood_type: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_verified: bool
    language: str

    model_config = {"from_attributes": True}


class PatientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    governorate: Optional[str] = Field(None, min_length=2, max_length=100)
    blood_type: Optional[str] = Field(None, max_length=5)
