"""Authentication service — registration, login, token management."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, Patient, Doctor, UserRole, VerificationStatus
from app.models.auth import RefreshToken
from app.models.specialty import Specialty


class AuthService:
    """Handles user authentication, registration, and token management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registration ──

    async def register_patient(
        self,
        name: str,
        email: str,
        phone: str,
        password: str,
        governorate: str,
    ) -> dict:
        """Register a new patient. Returns user + tokens."""
        # Check duplicates
        await self._check_email_exists(email)
        await self._check_phone_exists(phone)

        # Create user
        user = User(
            name=name,
            email=email.lower().strip(),
            phone=phone.strip(),
            password_hash=hash_password(password),
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Create patient profile
        patient = Patient(
            id=user.id,
            governorate=governorate,
        )
        self.db.add(patient)
        await self.db.flush()

        # Generate tokens
        tokens = await self._create_token_pair(user)

        return {
            "user": user,
            "patient": patient,
            "tokens": tokens,
        }

    async def register_doctor(
        self,
        name: str,
        email: str,
        phone: str,
        password: str,
        specialty_id: uuid.UUID,
        license_number: str,
        experience_years: int,
        bio: Optional[str] = None,
    ) -> dict:
        """Register a new doctor. Doctor starts in pending state."""
        # Check duplicates
        await self._check_email_exists(email)
        await self._check_phone_exists(phone)
        await self._check_license_exists(license_number)

        # Verify specialty exists
        specialty = await self.db.get(Specialty, specialty_id)
        if not specialty:
            raise ValueError("SPECIALTY_NOT_FOUND")

        # Create user
        user = User(
            name=name,
            email=email.lower().strip(),
            phone=phone.strip(),
            password_hash=hash_password(password),
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Create doctor profile
        doctor = Doctor(
            id=user.id,
            specialty_id=specialty_id,
            license_number=license_number.strip(),
            experience_years=experience_years,
            bio=bio,
            verification_status=VerificationStatus.PENDING,
        )
        self.db.add(doctor)
        await self.db.flush()

        return {
            "user": user,
            "doctor": doctor,
            "specialty": specialty,
        }

    # ── Login ──

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        user = await self._get_user_by_email(email)
        if not user:
            raise ValueError("INVALID_CREDENTIALS")

        if not verify_password(password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        if not user.is_active:
            raise ValueError("ACCOUNT_DISABLED")

        if user.deleted_at is not None:
            raise ValueError("ACCOUNT_DELETED")

        # Check doctor pending status
        if user.role == UserRole.DOCTOR and user.doctor:
            if user.doctor.verification_status == VerificationStatus.PENDING:
                raise ValueError("DOCTOR_PENDING_APPROVAL")
            if user.doctor.verification_status == VerificationStatus.REJECTED:
                raise ValueError("DOCTOR_REJECTED")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Generate tokens
        tokens = await self._create_token_pair(user)

        return {
            "user": user,
            "tokens": tokens,
        }

    # ── Token Refresh ──

    async def refresh_tokens(self, refresh_token_str: str) -> dict:
        """Validate refresh token and issue new token pair."""
        # Decode
        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("INVALID_REFRESH_TOKEN")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("INVALID_REFRESH_TOKEN")

        # Check token in DB
        token_hash = self._hash_token(refresh_token_str)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
            )
        )
        stored_token = result.scalar_one_or_none()
        if not stored_token:
            raise ValueError("REFRESH_TOKEN_REVOKED")

        # Revoke old token (single-use)
        stored_token.is_revoked = True
        await self.db.flush()

        # Get user
        user = await self.db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("USER_NOT_FOUND")

        # Issue new pair
        tokens = await self._create_token_pair(user)

        return {
            "user": user,
            "tokens": tokens,
        }

    # ── Logout ──

    async def logout(self, refresh_token_str: str) -> None:
        """Revoke a refresh token."""
        token_hash = self._hash_token(refresh_token_str)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored_token = result.scalar_one_or_none()
        if stored_token:
            stored_token.is_revoked = True
            await self.db.flush()

    # ── Get Current User ──

    async def get_current_user(self, token: str) -> Optional[User]:
        """Decode access token and return the user."""
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await self.db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active or user.deleted_at is not None:
            return None

        return user

    # ── Private Helpers ──

    async def _check_email_exists(self, email: str) -> None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        if result.scalar_one_or_none():
            raise ValueError("EMAIL_ALREADY_EXISTS")

    async def _check_phone_exists(self, phone: str) -> None:
        result = await self.db.execute(
            select(User).where(User.phone == phone.strip())
        )
        if result.scalar_one_or_none():
            raise ValueError("PHONE_ALREADY_EXISTS")

    async def _check_license_exists(self, license_number: str) -> None:
        result = await self.db.execute(
            select(Doctor).where(Doctor.license_number == license_number.strip())
        )
        if result.scalar_one_or_none():
            raise ValueError("LICENSE_ALREADY_EXISTS")

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def _create_token_pair(self, user: User) -> dict:
        """Create access + refresh tokens and store refresh in DB."""
        access = create_access_token(str(user.id), user.role.value)
        refresh = create_refresh_token(str(user.id))

        # Store refresh token hash
        stored = RefreshToken(
            user_id=user.id,
            token_hash=self._hash_token(refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
        self.db.add(stored)
        await self.db.flush()

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    @staticmethod
    def _hash_token(token: str) -> str:
        """SHA256 hash of a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
