"""PromoCode model."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, Boolean, Integer, Numeric, Enum, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class PromoType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PromoCode(Base, TimestampMixin):
    __tablename__ = "promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[PromoType] = mapped_column(
        Enum(PromoType, name="promo_type", create_constraint=True), nullable=False
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    max_discount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
