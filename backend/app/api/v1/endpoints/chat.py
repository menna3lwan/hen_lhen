"""Chat endpoints — rooms, messages, read receipts."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.schemas.chat import ChatRoomOut, SendMessageRequest, MessageOut
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.auth import MessageResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

ERROR_MAP = {
    "APPOINTMENT_NOT_FOUND": (404, "Appointment not found", "الموعد غير موجود"),
    "NOT_YOUR_APPOINTMENT": (403, "Not your appointment", "هذا ليس موعدك"),
    "APPOINTMENT_NOT_CONFIRMED": (400, "Appointment not confirmed yet", "الموعد لم يتم تأكيده بعد"),
    "ROOM_NOT_FOUND": (404, "Chat room not found", "غرفة المحادثة غير موجودة"),
    "NOT_YOUR_ROOM": (403, "Not your chat room", "هذه ليست غرفة محادثتك"),
    "ROOM_CLOSED": (400, "Chat room is closed", "غرفة المحادثة مغلقة"),
    "ONLY_DOCTOR_CAN_CLOSE": (403, "Only the doctor can close the room", "فقط الدكتورة يمكنها إغلاق المحادثة"),
}


def _raise(code: str):
    status, msg, msg_ar = ERROR_MAP[code]
    raise HTTPException(status_code=status, detail={
        "code": code, "message": msg, "message_ar": msg_ar,
    })


@router.post("/rooms", status_code=201)
async def get_or_create_room(
    appointment_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get or create a chat room for an appointment."""
    svc = ChatService(db)
    try:
        result = await svc.get_or_create_room(appointment_id, current_user.id)
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return result


@router.get("/rooms", response_model=PaginatedResponse)
async def list_rooms(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List chat rooms for current user."""
    svc = ChatService(db)
    data, total = await svc.list_rooms(current_user.id, page, limit)
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.post("/rooms/{room_id}/messages", status_code=201)
async def send_message(
    room_id: uuid.UUID,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a chat room."""
    svc = ChatService(db)
    try:
        result = await svc.send_message(
            room_id=room_id,
            sender_id=current_user.id,
            content=body.content,
            message_type=body.message_type,
            file_url=body.file_url,
        )
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return result


@router.get("/rooms/{room_id}/messages", response_model=PaginatedResponse)
async def list_messages(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List messages in a chat room."""
    svc = ChatService(db)
    try:
        data, total = await svc.list_messages(room_id, current_user.id, page, limit)
    except ValueError as e:
        _raise(str(e))
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.patch("/rooms/{room_id}/read", response_model=MessageResponse)
async def mark_read(
    room_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages in room as read."""
    svc = ChatService(db)
    try:
        count = await svc.mark_read(room_id, current_user.id)
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return MessageResponse(
        message=f"{count} messages marked as read",
        message_ar=f"تم تعليم {count} رسائل كمقروءة",
    )


@router.patch("/rooms/{room_id}/close")
async def close_room(
    room_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a chat room (doctor only)."""
    svc = ChatService(db)
    try:
        result = await svc.close_room(room_id, current_user.id)
    except ValueError as e:
        _raise(str(e))
    await db.commit()
    return result
