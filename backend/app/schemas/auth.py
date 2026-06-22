"""Auth request/response schemas."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──

class PatientRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    governorate: str = Field(..., min_length=2, max_length=100)


class DoctorRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    specialty_id: UUID
    license_number: str = Field(..., min_length=3, max_length=50)
    experience_years: int = Field(..., ge=0, le=60)
    bio: Optional[str] = Field(None, max_length=2000)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=128)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


# ── Response Schemas ──

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    role: str
    avatar_url: Optional[str] = None
    is_verified: bool
    language: str

    model_config = {"from_attributes": True}


class PatientResponse(UserResponse):
    governorate: str
    blood_type: Optional[str] = None


class DoctorResponse(UserResponse):
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
    verification_status: str


class PatientRegisterResponse(BaseModel):
    user: PatientResponse
    tokens: TokenResponse


class DoctorRegisterResponse(BaseModel):
    doctor: DoctorResponse
    status: str = "pending_approval"


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    message: str
    message_ar: Optional[str] = None
