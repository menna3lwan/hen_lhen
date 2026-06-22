"""Appointment model."""

import uuid
import enum
from datetime import date, time
from sqlalchemy import (
    String, Integer, ForeignKey, Text, Numeric, Date, Time, Enum, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class AppointmentType(str, enum.Enum):
    ONLINE = "online"
    CLINIC = "clinic"


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CancelledBy(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    SYSTEM = "system"


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("idx_appointments_patient", "patient_id", "status"),
        Index("idx_appointments_doctor", "doctor_id", "date", "status"),
        Index("idx_appointments_date", "date", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type", create_constraint=True),
        nullable=False,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status", create_constraint=True),
        default=AppointmentStatus.PENDING,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    promo_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("promo_codes.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[CancelledBy | None] = mapped_column(
        Enum(CancelledBy, name="cancelled_by_enum", create_constraint=True),
        nullable=True,
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship(back_populates="appointments", lazy="joined")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments", lazy="joined")
    branch: Mapped["Branch | None"] = relationship(lazy="joined")
    payment: Mapped["Payment | None"] = relationship(back_populates="appointment", uselist=False, lazy="selectin")
    chat_room: Mapped["ChatRoom | None"] = relationship(back_populates="appointment", uselist=False, lazy="noload")
    promo_code: Mapped["PromoCode | None"] = relationship(lazy="joined")
    review: Mapped["Review | None"] = relationship(back_populates="appointment", uselist=False, lazy="noload")


from app.models.user import Patient, Doctor
from app.models.branch import Branch
from app.models.payment import Payment
from app.models.chat import ChatRoom
from app.models.promo_code import PromoCode
from app.models.review import Review
