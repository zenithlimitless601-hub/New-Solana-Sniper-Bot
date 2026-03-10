"""WebSocket manager for real-time token broadcasting."""

from __future__ import annotations

import json
from collections import deque

from fastapi import WebSocket
from loguru import logger


class TokensWSManager:
    """Manages WebSocket connections and broadcasts new-token events.

    Maintains a ring-buffer backlog so that late-connecting clients
    receive recent token events on connect.
    """

    def __init__(self, buffer_size: int = 100) -> None:
        self._connections: set[WebSocket] = set()
        self._backlog: deque[str] = deque(maxlen=buffer_size)

    async def connect(self, websocket: WebSocket, *, send_backlog: bool = True) -> None:
        """Accept a WebSocket and optionally replay the backlog."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WS connected: total={count}", count=len(self._connections))
        if send_backlog and self._backlog:
            try:
                for message in list(self._backlog):
                    await websocket.send_text(message)
                logger.debug("WS backlog sent: items={n}", n=len(self._backlog))
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from the active connections set."""
        self._connections.discard(websocket)
        logger.info("WS disconnected: total={count}", count=len(self._connections))

    async def broadcast_new_token(self, payload: dict) -> None:
        """Broadcast a new_token event to all connected WebSocket clients."""
        if not self._connections:
            logger.debug("WS broadcast skipped: no connections")
        message = json.dumps({"event": "new_token", "data": payload})
        self._backlog.append(message)
        if not self._connections:
            return
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
        delivered = len(self._connections)
        logger.info(
            "WS broadcast new_token: delivered={delivered}, dropped={dropped}",
            delivered=delivered,
            dropped=len(dead),
        )

    def connections_count(self) -> int:
        """Return the number of active WebSocket connections."""
        return len(self._connections)
