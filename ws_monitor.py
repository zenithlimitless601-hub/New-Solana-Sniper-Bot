import asyncio
import json
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed


class WSMonitor:
    def __init__(self, url: str, retry_base: float = 1.0, retry_max: float = 30.0) -> None:
        self.url = url
        self.retry_base = retry_base
        self.retry_max = retry_max

    async def run(self) -> None:
        delay = self.retry_base
        while True:
            try:
                await self._listen_once()
                delay = self.retry_base
            except (ConnectionClosed, OSError):
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.retry_max)
            except KeyboardInterrupt:
                break

    async def _listen_once(self) -> None:
        async with websockets.connect(
            self.url,
            max_queue=None,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:
            while True:
                msg = await ws.recv()
                self._handle_message(msg)

    def _handle_message(self, msg: str) -> None:
        evt: dict[str, Any] = json.loads(msg)
        if evt.get("event") == "new_token":
            data = evt.get("data", {})
            print(
                f"{data.get('id')} | {data.get('address')} | "
                f"{data.get('symbol') or ''} | {data.get('name') or ''}"
            )


if __name__ == "__main__":
    asyncio.run(WSMonitor("ws://localhost:8000/api/v1/ws/tokens").run())
