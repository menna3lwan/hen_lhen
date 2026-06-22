"""WebSocket verification — connection, auth, messaging."""

import uuid
import pytest
import pytest_asyncio
from app.core.websocket_manager import ConnectionManager

pytestmark = pytest.mark.asyncio


class TestConnectionManager:
    """Unit tests for the WebSocket connection manager."""

    def test_initial_state(self):
        mgr = ConnectionManager()
        assert mgr.active_rooms == 0
        assert mgr.total_connections == 0

    async def test_connect_and_disconnect(self):
        mgr = ConnectionManager()
        room_id = uuid.uuid4()
        user_id = uuid.uuid4()

        class FakeWS:
            accepted = False
            async def accept(self): self.accepted = True
            async def send_text(self, text): pass

        ws = FakeWS()
        await mgr.connect(ws, room_id, user_id)
        assert mgr.active_rooms == 1
        assert mgr.total_connections == 1
        assert mgr.is_user_online(user_id) is True

        mgr.disconnect(ws, room_id, user_id)
        assert mgr.active_rooms == 0
        assert mgr.total_connections == 0
        assert mgr.is_user_online(user_id) is False

    async def test_multi_device_same_user(self):
        mgr = ConnectionManager()
        room_id = uuid.uuid4()
        user_id = uuid.uuid4()

        class FakeWS:
            async def accept(self): pass
            async def send_text(self, text): pass

        ws1, ws2 = FakeWS(), FakeWS()
        await mgr.connect(ws1, room_id, user_id)
        await mgr.connect(ws2, room_id, user_id)

        assert mgr.total_connections == 2
        assert mgr.is_user_online(user_id) is True

        # Disconnect one → still online
        mgr.disconnect(ws1, room_id, user_id)
        assert mgr.is_user_online(user_id) is True
        assert mgr.total_connections == 1

        # Disconnect last → offline
        mgr.disconnect(ws2, room_id, user_id)
        assert mgr.is_user_online(user_id) is False

    async def test_broadcast_excludes_sender(self):
        mgr = ConnectionManager()
        room_id = uuid.uuid4()
        sender_id = uuid.uuid4()
        receiver_id = uuid.uuid4()

        received = []

        class FakeWS:
            async def accept(self): pass
            async def send_text(self, text): received.append(text)

        ws_sender = FakeWS()
        ws_receiver = FakeWS()

        await mgr.connect(ws_sender, room_id, sender_id)
        await mgr.connect(ws_receiver, room_id, receiver_id)

        await mgr.broadcast_to_room(room_id, {"msg": "hello"}, exclude_user=sender_id)

        # Only receiver should get it
        assert len(received) == 1

    async def test_broadcast_handles_dead_connections(self):
        mgr = ConnectionManager()
        room_id = uuid.uuid4()
        user_id = uuid.uuid4()

        class DeadWS:
            async def accept(self): pass
            async def send_text(self, text): raise ConnectionError("dead")

        ws = DeadWS()
        await mgr.connect(ws, room_id, user_id)
        # Should not raise
        await mgr.broadcast_to_room(room_id, {"msg": "test"})

    async def test_send_to_offline_user(self):
        mgr = ConnectionManager()
        # Should not raise
        await mgr.send_to_user(uuid.uuid4(), {"msg": "test"})

    async def test_multiple_rooms(self):
        mgr = ConnectionManager()
        user_id = uuid.uuid4()
        room1, room2 = uuid.uuid4(), uuid.uuid4()

        class FakeWS:
            async def accept(self): pass
            async def send_text(self, text): pass

        ws1, ws2 = FakeWS(), FakeWS()
        await mgr.connect(ws1, room1, user_id)
        await mgr.connect(ws2, room2, user_id)
        assert mgr.active_rooms == 2

        mgr.disconnect(ws1, room1, user_id)
        assert mgr.active_rooms == 1

    async def test_no_zombie_connections_after_disconnect(self):
        """Verify no memory leaks from orphaned connections."""
        mgr = ConnectionManager()

        class FakeWS:
            async def accept(self): pass
            async def send_text(self, text): pass

        for _ in range(100):
            room_id = uuid.uuid4()
            user_id = uuid.uuid4()
            ws = FakeWS()
            await mgr.connect(ws, room_id, user_id)
            mgr.disconnect(ws, room_id, user_id)

        assert mgr.active_rooms == 0
        assert mgr.total_connections == 0


class TestWebSocketAuth:
    """Test JWT validation for WebSocket connections."""

    async def test_invalid_token_rejected(self, client):
        """WS with invalid token should close with 4001."""
        from app.core.security import settings
        # We can't easily test WS via httpx, but we can verify the token validation logic
        from app.core.security import decode_token
        assert decode_token("invalid.jwt.token") is None

    async def test_expired_token_rejected(self):
        from jose import jwt
        from datetime import datetime, timedelta, timezone
        from app.core.config import settings

        expired_payload = {
            "sub": str(uuid.uuid4()),
            "role": "patient",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        from app.core.security import decode_token
        assert decode_token(expired_token) is None

    async def test_valid_token_accepted(self):
        from app.core.security import create_access_token, decode_token
        uid = str(uuid.uuid4())
        token = create_access_token(uid, "patient")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == uid
