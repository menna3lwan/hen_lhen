"""Review model — patient reviews on doctors."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    ForeignKey, Text, Numeric, DateTime, Index, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("appointment_id", name="uq_review_appointment"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
        Index("idx_reviews_doctor", "doctor_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True
    )
    rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship(back_populates="reviews")
    patient: Mapped["Patient"] = relationship(lazy="joined")
    appointment: Mapped["Appointment | None"] = relationship(back_populates="review")


from app.models.user import Doctor, Patient
from app.models.appointment import Appointment
