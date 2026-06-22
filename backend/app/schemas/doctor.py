"""Doctor schemas."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class DoctorListQuery(BaseModel):
    """Query params for doctor listing."""
    specialty: Optional[str] = None
    search: Optional[str] = None
    sort: Optional[str] = Field(None, pattern="^(rating|fee|experience)$")
    order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    online: Optional[bool] = None
    governorate: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class DoctorBranchOut(BaseModel):
    id: UUID
    name: str
    governorate: str
    area: str
    address: str
    phone: str
    consultation_fee: float
    is_active: bool

    model_config = {"from_attributes": True}


class DoctorProfileOut(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    avatar_url: Optional[str] = None
    specialty_id: UUID
    specialty_name_ar: Optional[str] = None
    specialty_name_en: Optional[str] = None
    license_number: str
    experience_years: int
    bio: Optional[str] = None
    consultation_fee: float
    rating: float
    reviews_count: int
    patients_count: int
    is_online: bool
    is_verified: bool
    verification_status: str
    branches: List[DoctorBranchOut] = []

    model_config = {"from_attributes": True}


class DoctorListItemOut(BaseModel):
    id: UUID
    name: str
    avatar_url: Optional[str] = None
    specialty_name_ar: Optional[str] = None
    specialty_name_en: Optional[str] = None
    consultation_fee: float
    rating: float
    reviews_count: int
    experience_years: int
    patients_count: int
    is_online: bool
    is_verified: bool

    model_config = {"from_attributes": True}


class DoctorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    bio: Optional[str] = Field(None, max_length=2000)
    consultation_fee: Optional[float] = Field(None, ge=0)


class DoctorOnlineStatusRequest(BaseModel):
    is_online: bool


class TimeSlotOut(BaseModel):
    time: str
    is_available: bool


class AvailabilityOut(BaseModel):
    slots: List[TimeSlotOut]
