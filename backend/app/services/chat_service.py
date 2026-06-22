"""Chat service — rooms, messages, read receipts."""

import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatRoom, Message, ChatStatus, MessageType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_room(
        self,
        appointment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Get existing chat room or create one for the appointment."""
        # Check appointment exists and user is participant
        appt = await self.db.get(Appointment, appointment_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.patient_id != user_id and appt.doctor_id != user_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")
        if appt.status not in (AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED):
            raise ValueError("APPOINTMENT_NOT_CONFIRMED")

        # Check for existing room
        result = await self.db.execute(
            select(ChatRoom).where(ChatRoom.appointment_id == appointment_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            room = ChatRoom(
                appointment_id=appointment_id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                status=ChatStatus.ACTIVE,
            )
            self.db.add(room)
            await self.db.flush()

        return await self._format_room(room, user_id)

    async def list_rooms(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """List chat rooms for a user (patient or doctor)."""
        base = select(ChatRoom).where(
            or_(
                ChatRoom.patient_id == user_id,
                ChatRoom.doctor_id == user_id,
            )
        )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(ChatRoom.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        rooms = result.scalars().all()

        data = []
        for room in rooms:
            data.append(await self._format_room(room, user_id))

        return data, total

    async def send_message(
        self,
        room_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        message_type: str = "text",
        file_url: Optional[str] = None,
    ) -> dict:
        """Send a message in a chat room."""
        room = await self.db.get(ChatRoom, room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.patient_id != sender_id and room.doctor_id != sender_id:
            raise ValueError("NOT_YOUR_ROOM")
        if room.status != ChatStatus.ACTIVE:
            raise ValueError("ROOM_CLOSED")

        msg = Message(
            chat_room_id=room_id,
            sender_id=sender_id,
            content=content,
            type=MessageType(message_type),
            media_url=file_url,
        )
        self.db.add(msg)

        # Update room metadata
        room.last_message = content[:100]
        room.last_message_at = datetime.now(timezone.utc)

        await self.db.flush()

        sender = await self.db.get(User, sender_id)
        return self._format_message(msg, sender.name if sender else None)

    async def list_messages(
        self,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[dict], int]:
        """List messages in a chat room."""
        room = await self.db.get(ChatRoom, room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.patient_id != user_id and room.doctor_id != user_id:
            raise ValueError("NOT_YOUR_ROOM")

        base = select(Message).where(Message.chat_room_id == room_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(Message.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Load sender names
        sender_ids = list({m.sender_id for m in messages})
        users_map = {}
        if sender_ids:
            users_result = await self.db.execute(
                select(User).where(User.id.in_(sender_ids))
            )
            for u in users_result.scalars().all():
                users_map[u.id] = u.name

        data = [
            self._format_message(m, users_map.get(m.sender_id))
            for m in reversed(messages)  # chronological order
        ]
        return data, total

    async def mark_read(
        self,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """Mark all messages in room as read by user."""
        room = await self.db.get(ChatRoom, room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.patient_id != user_id and room.doctor_id != user_id:
            raise ValueError("NOT_YOUR_ROOM")

        result = await self.db.execute(
            select(Message).where(
                Message.chat_room_id == room_id,
                Message.sender_id != user_id,
                Message.is_read == False,
            )
        )
        unread = result.scalars().all()
        for msg in unread:
            msg.is_read = True
        await self.db.flush()
        return len(unread)

    async def close_room(
        self, room_id: uuid.UUID, user_id: uuid.UUID,
    ) -> dict:
        """Close a chat room (doctor only or admin)."""
        room = await self.db.get(ChatRoom, room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.doctor_id != user_id:
            raise ValueError("ONLY_DOCTOR_CAN_CLOSE")

        room.status = ChatStatus.CLOSED
        room.closed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return await self._format_room(room, user_id)

    async def _format_room(self, room: ChatRoom, current_user_id: uuid.UUID) -> dict:
        """Format room with names and unread count."""
        # Load names
        patient = await self.db.get(User, room.patient_id)
        doctor = await self.db.get(User, room.doctor_id)

        # Unread count
        unread_q = select(func.count()).where(
            Message.chat_room_id == room.id,
            Message.sender_id != current_user_id,
            Message.is_read == False,
        )
        unread = (await self.db.execute(unread_q)).scalar() or 0

        return {
            "id": room.id,
            "appointment_id": room.appointment_id,
            "patient_id": room.patient_id,
            "doctor_id": room.doctor_id,
            "patient_name": patient.name if patient else None,
            "doctor_name": doctor.name if doctor else None,
            "status": room.status.value,
            "last_message": room.last_message,
            "last_message_at": room.last_message_at.isoformat() if room.last_message_at else None,
            "unread_count": unread,
            "created_at": room.created_at.isoformat() if room.created_at else "",
        }

    @staticmethod
    def _format_message(m: Message, sender_name: Optional[str] = None) -> dict:
        return {
            "id": m.id,
            "chat_room_id": m.chat_room_id,
            "sender_id": m.sender_id,
            "sender_name": sender_name,
            "content": m.content,
            "message_type": m.type.value,
            "file_url": m.media_url,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
