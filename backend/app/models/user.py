"""User, Patient, Doctor, Admin models."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, Enum, ForeignKey, Text,
    Numeric, DateTime, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin, SoftDeleteMixin


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="ar", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(back_populates="user", uselist=False, lazy="selectin")
    doctor: Mapped["Doctor"] = relationship(
        back_populates="user", uselist=False, lazy="selectin",
        foreign_keys="[Doctor.id]",
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", lazy="noload")
    devices: Mapped[list["Device"]] = relationship(back_populates="user", lazy="noload")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", lazy="noload")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    governorate: Mapped[str] = mapped_column(String(100), nullable=False)
    blood_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="patient", lazy="joined")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient", lazy="noload")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="patient", lazy="noload")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    specialty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specialties.id"), nullable=False
    )
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultation_fee: Mapped[float] = mapped_column(
        Numeric(10, 2), default=200.00, nullable=False
    )
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.00, nullable=False)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    patients_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", create_constraint=True),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="doctor", lazy="joined",
        foreign_keys="[Doctor.id]",
    )
    specialty: Mapped["Specialty"] = relationship(back_populates="doctors", lazy="joined")
    branches: Mapped[list["Branch"]] = relationship(back_populates="doctor", lazy="noload")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor", lazy="noload")
    reviews: Mapped[list["Review"]] = relationship(back_populates="doctor", lazy="noload")


# Avoid circular imports — these are resolved at runtime
from app.models.notification import Notification
from app.models.device import Device
from app.models.auth import RefreshToken
from app.models.appointment import Appointment
from app.models.favorite import Favorite
from app.models.specialty import Specialty
from app.models.branch import Branch
from app.models.review import Review
