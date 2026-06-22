"""WebSocket connection manager for real-time chat."""

import json
import uuid
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections per chat room."""

    def __init__(self):
        # room_id -> set of (user_id, websocket)
        self._rooms: Dict[uuid.UUID, Set[tuple]] = {}
        # user_id -> set of websockets (user can be in multiple rooms)
        self._user_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(
        self, websocket: WebSocket, room_id: uuid.UUID, user_id: uuid.UUID,
    ):
        """Accept and register a WebSocket connection."""
        await websocket.accept()

        if room_id not in self._rooms:
            self._rooms[room_id] = set()
        self._rooms[room_id].add((user_id, websocket))

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)

    def disconnect(
        self, websocket: WebSocket, room_id: uuid.UUID, user_id: uuid.UUID,
    ):
        """Remove a WebSocket connection."""
        if room_id in self._rooms:
            self._rooms[room_id].discard((user_id, websocket))
            if not self._rooms[room_id]:
                del self._rooms[room_id]

        if user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

    async def broadcast_to_room(
        self, room_id: uuid.UUID, message: dict, exclude_user: uuid.UUID = None,
    ):
        """Send a message to all connections in a room."""
        if room_id not in self._rooms:
            return

        payload = json.dumps(message, default=str)
        dead = []
        for user_id, ws in self._rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append((user_id, ws))

        # Clean up dead connections
        for item in dead:
            self._rooms[room_id].discard(item)

    async def send_to_user(self, user_id: uuid.UUID, message: dict):
        """Send a message to all connections of a specific user."""
        if user_id not in self._user_connections:
            return

        payload = json.dumps(message, default=str)
        dead = []
        for ws in self._user_connections[user_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._user_connections[user_id].discard(ws)

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        return bool(self._user_connections.get(user_id))

    @property
    def active_rooms(self) -> int:
        return len(self._rooms)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._user_connections.values())


# Singleton instance
ws_manager = ConnectionManager()
