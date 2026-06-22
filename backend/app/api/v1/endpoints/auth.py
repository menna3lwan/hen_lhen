"""Auth endpoints — register, login, refresh, logout."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    PatientRegisterRequest,
    DoctorRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    PatientRegisterResponse,
    PatientResponse,
    DoctorRegisterResponse,
    DoctorResponse,
    LoginResponse,
    TokenResponse,
    UserResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Error code → (status, message_en, message_ar)
ERROR_MAP = {
    "EMAIL_ALREADY_EXISTS": (409, "Email already registered", "البريد الإلكتروني مسجل بالفعل"),
    "PHONE_ALREADY_EXISTS": (409, "Phone number already registered", "رقم الهاتف مسجل بالفعل"),
    "LICENSE_ALREADY_EXISTS": (409, "License number already registered", "رقم الترخيص مسجل بالفعل"),
    "SPECIALTY_NOT_FOUND": (400, "Specialty not found", "التخصص غير موجود"),
    "INVALID_CREDENTIALS": (401, "Invalid email or password", "بريد إلكتروني أو كلمة مرور غير صحيحة"),
    "ACCOUNT_DISABLED": (403, "Account is disabled", "الحساب معطل"),
    "ACCOUNT_DELETED": (403, "Account has been deleted", "الحساب محذوف"),
    "DOCTOR_PENDING_APPROVAL": (403, "Account pending approval", "الحساب في انتظار الموافقة"),
    "DOCTOR_REJECTED": (403, "Account application rejected", "تم رفض طلب الحساب"),
    "INVALID_REFRESH_TOKEN": (401, "Invalid refresh token", "رمز التحديث غير صالح"),
    "REFRESH_TOKEN_REVOKED": (401, "Refresh token has been revoked", "رمز التحديث ملغي"),
    "USER_NOT_FOUND": (404, "User not found", "المستخدم غير موجود"),
}


def _raise_error(code: str):
    """Raise HTTPException from error code."""
    status_code, message, message_ar = ERROR_MAP.get(code, (400, code, code))
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "message_ar": message_ar},
    )


@router.post("/register/patient", response_model=PatientRegisterResponse, status_code=201)
async def register_patient(
    body: PatientRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new patient account."""
    service = AuthService(db)
    try:
        result = await service.register_patient(
            name=body.name,
            email=body.email,
            phone=body.phone,
            password=body.password,
            governorate=body.governorate,
        )
    except ValueError as e:
        _raise_error(str(e))

    user = result["user"]
    patient = result["patient"]
    return PatientRegisterResponse(
        user=PatientResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            language=user.language,
            governorate=patient.governorate,
            blood_type=patient.blood_type,
        ),
        tokens=TokenResponse(**result["tokens"]),
    )


@router.post("/register/doctor", response_model=DoctorRegisterResponse, status_code=201)
async def register_doctor(
    body: DoctorRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new doctor account (pending approval)."""
    service = AuthService(db)
    try:
        result = await service.register_doctor(
            name=body.name,
            email=body.email,
            phone=body.phone,
            password=body.password,
            specialty_id=body.specialty_id,
            license_number=body.license_number,
            experience_years=body.experience_years,
            bio=body.bio,
        )
    except ValueError as e:
        _raise_error(str(e))

    user = result["user"]
    doctor = result["doctor"]
    specialty = result["specialty"]
    return DoctorRegisterResponse(
        doctor=DoctorResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            language=user.language,
            specialty_id=doctor.specialty_id,
            specialty_name_ar=specialty.name_ar if specialty else None,
            specialty_name_en=specialty.name_en if specialty else None,
            license_number=doctor.license_number,
            experience_years=doctor.experience_years,
            bio=doctor.bio,
            consultation_fee=float(doctor.consultation_fee),
            rating=float(doctor.rating),
            reviews_count=doctor.reviews_count,
            patients_count=doctor.patients_count,
            is_online=doctor.is_online,
            verification_status=doctor.verification_status.value,
        ),
        status="pending_approval",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    service = AuthService(db)
    try:
        result = await service.login(email=body.email, password=body.password)
    except ValueError as e:
        _raise_error(str(e))

    user = result["user"]
    return LoginResponse(
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            language=user.language,
        ),
        tokens=TokenResponse(**result["tokens"]),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    service = AuthService(db)
    try:
        result = await service.refresh_tokens(body.refresh_token)
    except ValueError as e:
        _raise_error(str(e))

    return TokenResponse(**result["tokens"])


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Logout — revoke refresh token."""
    service = AuthService(db)
    await service.logout(body.refresh_token)
    return MessageResponse(message="Logged out successfully", message_ar="تم تسجيل الخروج بنجاح")
