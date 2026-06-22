"""Medical Record & Prescription models."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, ForeignKey, Text, Enum, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class RecordType(str, enum.Enum):
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    DIAGNOSIS = "diagnosis"
    FOLLOW_UP = "follow_up"


class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"
    __table_args__ = (
        Index("idx_medical_records_patient", "patient_id", "created_at"),
        Index("idx_medical_records_doctor", "doctor_id", "created_at"),
        Index("idx_medical_records_appointment", "appointment_id"),
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
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False
    )
    type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, name="record_type", create_constraint=True),
        nullable=False,
    )
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescriptions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attachments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_private: Mapped[bool] = mapped_column(default=False, nullable=False)
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    appointment: Mapped["Appointment"] = relationship(lazy="joined")
    patient: Mapped["Patient"] = relationship(lazy="joined")
    doctor: Mapped["Doctor"] = relationship(
        lazy="joined", foreign_keys=[doctor_id],
    )


from app.models.appointment import Appointment
from app.models.user import Patient, Doctor
