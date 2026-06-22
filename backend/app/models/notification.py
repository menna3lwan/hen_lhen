"""Notification model."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, ForeignKey, Text, Enum, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base


class NotificationType(str, enum.Enum):
    APPOINTMENT = "appointment"
    MESSAGE = "message"
    PROMOTION = "promotion"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user", "user_id", "is_read", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", create_constraint=True),
        nullable=False,
    )
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")


from app.models.user import User
