"""Payment model."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, ForeignKey, Numeric, Enum, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payments_appointment", "appointment_id"),
        Index("idx_payments_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", create_constraint=True),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Relationships
    appointment: Mapped["Appointment"] = relationship(back_populates="payment")


from app.models.appointment import Appointment
