"""API dependencies — auth, DB session, current user."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_AUTHENTICATED", "message": "Authentication required", "message_ar": "يجب تسجيل الدخول"},
        )

    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token", "message_ar": "رمز غير صالح أو منتهي الصلاحية"},
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account is disabled", "message_ar": "الحساب معطل"},
        )
    return current_user


async def get_current_patient(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure the user is a patient."""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_PATIENT", "message": "Patient access required", "message_ar": "صلاحية المريضة مطلوبة"},
        )
    return current_user


async def get_current_doctor(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure the user is an approved doctor."""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_DOCTOR", "message": "Doctor access required", "message_ar": "صلاحية الدكتورة مطلوبة"},
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure the user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ADMIN", "message": "Admin access required", "message_ar": "صلاحية المسؤول مطلوبة"},
        )
    return current_user
