"""ChatRoom and Message models."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, ForeignKey, Text, Enum, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class ChatStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        Index("idx_chatrooms_participants", "patient_id", "doctor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), unique=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False
    )
    status: Mapped[ChatStatus] = mapped_column(
        Enum(ChatStatus, name="chat_status", create_constraint=True),
        default=ChatStatus.ACTIVE,
        nullable=False,
    )
    last_message: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    appointment: Mapped["Appointment"] = relationship(back_populates="chat_room")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat_room", lazy="noload", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_chatroom", "chat_room_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type", create_constraint=True),
        default=MessageType.TEXT,
        nullable=False,
    )
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    chat_room: Mapped["ChatRoom"] = relationship(back_populates="messages")


from app.models.appointment import Appointment
