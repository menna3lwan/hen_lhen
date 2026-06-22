"""Chat schemas."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRoomOut(BaseModel):
    id: UUID
    appointment_id: UUID
    patient_id: UUID
    doctor_id: UUID
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    status: str
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0
    created_at: str


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field("text", pattern="^(text|image|file|voice)$")
    file_url: Optional[str] = None


class MessageOut(BaseModel):
    id: UUID
    chat_room_id: UUID
    sender_id: UUID
    sender_name: Optional[str] = None
    content: str
    message_type: str
    file_url: Optional[str] = None
    is_read: bool = False
    created_at: str
