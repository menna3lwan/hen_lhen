"""Device model — FCM/APNs token storage."""

import uuid
import enum
from sqlalchemy import String, Boolean, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class DevicePlatform(str, enum.Enum):
    IOS = "ios"
    ANDROID = "android"


class Device(Base, TimestampMixin):
    __tablename__ = "devices"
    __table_args__ = (
        Index("idx_devices_user", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    platform: Mapped[DevicePlatform] = mapped_column(
        Enum(DevicePlatform, name="device_platform", create_constraint=True),
        nullable=False,
    )
    fcm_token: Mapped[str] = mapped_column(String(500), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="devices")


from app.models.user import User
