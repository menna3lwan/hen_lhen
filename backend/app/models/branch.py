"""Branch and BranchSchedule models."""

import uuid
import enum
from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, Numeric, Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin, SoftDeleteMixin


class Branch(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    governorate: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    consultation_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    doctor: Mapped["Doctor"] = relationship(back_populates="branches", lazy="joined")
    schedules: Mapped[list["BranchSchedule"]] = relationship(
        back_populates="branch", lazy="selectin", cascade="all, delete-orphan"
    )


class BranchSchedule(Base):
    __tablename__ = "branch_schedules"
    __table_args__ = (
        UniqueConstraint("branch_id", "day_of_week", name="uq_branch_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Sat, 6=Fri
    start_time = mapped_column(Time, nullable=False)
    end_time = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    branch: Mapped["Branch"] = relationship(back_populates="schedules")


from app.models.user import Doctor
