"""Branch schemas."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ScheduleIn(BaseModel):
    day: int = Field(..., ge=0, le=6)  # 0=Sat, 6=Fri
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    slot_duration: int = Field(30, ge=10, le=120)


class BranchCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    governorate: str = Field(..., min_length=2, max_length=100)
    area: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5)
    phone: str = Field(..., min_length=10, max_length=20)
    consultation_fee: float = Field(..., ge=0)
    working_days: List[ScheduleIn] = Field(..., min_length=1)


class BranchUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    governorate: Optional[str] = Field(None, min_length=2, max_length=100)
    area: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    consultation_fee: Optional[float] = Field(None, ge=0)
    working_days: Optional[List[ScheduleIn]] = None


class ScheduleOut(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int
    is_active: bool

    model_config = {"from_attributes": True}


class BranchOut(BaseModel):
    id: UUID
    name: str
    governorate: str
    area: str
    address: str
    phone: str
    consultation_fee: float
    is_active: bool
    schedules: List[ScheduleOut] = []

    model_config = {"from_attributes": True}
