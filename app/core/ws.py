from __future__ import annotations

import json
from typing import Set

from fastapi import WebSocket
from loguru import logger
from collections import deque


class TokensWSManager:
    def __init__(self, buffer_size: int = 100) -> None:
        self._connections: set[WebSocket] = set()
        self._backlog = deque(maxlen=buffer_size)

    async def connect(self, websocket: WebSocket, send_backlog: bool = True) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WS connected: total={count}", count=len(self._connections))
        if send_backlog and self._backlog:
            try:
                for message in list(self._backlog):
                    await websocket.send_text(message)
                logger.debug(
                    "WS backlog sent: items={n}",
                    n=len(self._backlog),
                )
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("WS disconnected: total={count}", count=len(self._connections))

    async def broadcast_new_token(self, payload: dict) -> None:
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
        if dead:
            for ws in dead:
                self.disconnect(ws)
        delivered = len(self._connections) - len(dead)
        logger.info(
            "WS broadcast new_token: delivered={delivered}, dropped={dropped}",
            delivered=delivered,
            dropped=len(dead),
        )

    def connections_count(self) -> int:
        return len(self._connections)
