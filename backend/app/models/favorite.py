"""Favorite model — patient favorite doctors."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base


class Favorite(Base):
    __tablename__ = "favorites"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), primary_key=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(back_populates="favorites")
    doctor: Mapped["Doctor"] = relationship(lazy="joined")


from app.models.user import Patient, Doctor
