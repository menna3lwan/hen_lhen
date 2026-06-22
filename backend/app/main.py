"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.security import decode_token
from app.core.websocket_manager import ws_manager
from app.core.cache import cache
from app.api.v1.router import api_router
from app.db.session import AsyncSessionLocal
from app.services.chat_service import ChatService
from app.services.notification_service import notify_new_message
from app.middleware.error_handler import (
    validation_exception_handler,
    integrity_error_handler,
    generic_exception_handler,
)
from app.middleware.security_headers import SecurityHeadersMiddleware


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await cache.connect()
    cache_status = "connected" if cache.is_connected else "fallback (in-memory)"
    print(f"🚀 {settings.APP_NAME} API starting — {settings.APP_ENV} | cache: {cache_status}")
    yield
    # Shutdown
    await cache.close()
    print(f"👋 {settings.APP_NAME} API shutting down")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        description="هُنَّ لَهُنَّ — Medical Consultation Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # State
    app.state.limiter = limiter

    # Middleware (order matters — last added = first executed)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Routes
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # ── WebSocket endpoint for real-time chat ──

    @app.websocket("/ws/chat/{room_id}")
    async def websocket_chat(
        websocket: WebSocket,
        room_id: uuid.UUID,
        token: str = Query(...),
    ):
        """WebSocket endpoint for real-time chat.

        Connect: ws://host/ws/chat/{room_id}?token=<jwt_access_token>
        Send: {"content": "message text", "message_type": "text"}
        Receive: {"type": "message", "data": {...}} or {"type": "read", "data": {...}}
        """
        # Authenticate via JWT token in query param
        try:
            payload = decode_token(token)
            user_id = uuid.UUID(payload["sub"])
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Verify user belongs to this room
        async with AsyncSessionLocal() as db:
            svc = ChatService(db)
            try:
                from app.models.chat import ChatRoom
                room = await db.get(ChatRoom, room_id)
                if not room or (room.patient_id != user_id and room.doctor_id != user_id):
                    await websocket.close(code=4003, reason="Not your room")
                    return
            except Exception:
                await websocket.close(code=4000, reason="Room error")
                return

        # Connect
        await ws_manager.connect(websocket, room_id, user_id)

        try:
            while True:
                data = await websocket.receive_json()

                content = data.get("content", "").strip()
                message_type = data.get("message_type", "text")
                file_url = data.get("file_url")

                if not content:
                    continue

                # Persist message
                async with AsyncSessionLocal() as db:
                    svc = ChatService(db)
                    msg = await svc.send_message(
                        room_id=room_id,
                        sender_id=user_id,
                        content=content,
                        message_type=message_type,
                        file_url=file_url,
                    )
                    await db.commit()

                    # Determine recipient for push notification
                    room = await db.get(ChatRoom, room_id)
                    recipient_id = room.doctor_id if user_id == room.patient_id else room.patient_id

                    # Push notification if recipient offline
                    if not ws_manager.is_user_online(recipient_id):
                        from app.models.user import User
                        sender = await db.get(User, user_id)
                        sender_name = sender.name if sender else "مستخدم"
                        await notify_new_message(db, recipient_id, sender_name, room_id)
                        await db.commit()

                # Broadcast to room
                await ws_manager.broadcast_to_room(
                    room_id,
                    {"type": "message", "data": msg},
                )

        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, room_id, user_id)
        except Exception:
            ws_manager.disconnect(websocket, room_id, user_id)

    return app


app = create_app()
