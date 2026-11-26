
import asyncio
import json
import logging
import os
import random
import time

import websockets

logger = logging.getLogger(__name__)

BASE_URL = "wss://pumpportal.fun/api/data"


class PumpPortalClient:

    def __init__(self, on_event):
        self.on_event = on_event

        self.ws = None
        self.stop_event = asyncio.Event()

        self.tracked_mints = set()
        self.seen_creations = set()

        self.send_lock = asyncio.Lock()

        self.last_event_time = None
        self.connected = False

    def get_url(self):

        api_key = os.getenv("PUMPPORTAL_API_KEY")

        if api_key:
            return f"{BASE_URL}?api-key={api_key}"

        return BASE_URL

    async def send(self, payload):

        if not self.ws:
            return

        async with self.send_lock:
            await self.ws.send(json.dumps(payload))

    async def subscribe_new_tokens(self):

        await self.send({
            "method": "subscribeNewToken"
        })

        logger.info("Subscribed to new token stream")

    async def subscribe_migration(self):

        await self.send({
            "method": "subscribeMigration"
        })

        logger.info("Subscribed to migration stream")

    async def watch_token(self, mint):

        if mint in self.tracked_mints:
            return

        self.tracked_mints.add(mint)

        if self.ws:

            await self.send({
                "method": "subscribeTokenTrade",
                "keys": [mint]
            })

            logger.info("Subscribed to trades: %s", mint)

    async def handle_message(self, raw):

        try:
            event = json.loads(raw)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received")
            return

        self.last_event_time = time.time()

        # Ignore subscription acknowledgements and control messages.
        if "txType" not in event:
            logger.debug("Control message: %s", event)
            return

        tx_type = event.get("txType")
        mint = event.get("mint")

        if not mint:
            return

        if tx_type == "create":

            if mint in self.seen_creations:
                return

            self.seen_creations.add(mint)

            await self.on_event("new_token", event)

        elif tx_type in ("buy", "sell"):

            await self.on_event("trade", event)

        elif tx_type in ("migrate", "migration"):

            await self.on_event("migration", event)

    async def run_forever(self):

        backoff = 2

        while not self.stop_event.is_set():

            try:

                logger.info("Connecting to PumpPortal...")

                async with websockets.connect(
                    self.get_url(),
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                    max_size=2**22
                ) as websocket:

                    self.ws = websocket
                    self.connected = True

                    logger.info("PumpPortal connected")

                    # Subscribe to the main streams.
                    await self.subscribe_new_tokens()
                    await self.subscribe_migration()

                    # Restore token subscriptions after reconnect.
                    if self.tracked_mints:

                        await self.send({
                            "method": "subscribeTokenTrade",
                            "keys": list(self.tracked_mints)
                        })

                    backoff = 2

                    async for raw in websocket:

                        if self.stop_event.is_set():
                            break

                        await self.handle_message(raw)

            except asyncio.CancelledError:
                raise

            except Exception:

                logger.exception("PumpPortal connection error")

            finally:

                self.ws = None
                self.connected = False

            if not self.stop_event.is_set():

                delay = backoff + random.uniform(0, 1)

                logger.warning(
                    "Reconnecting in %.1f seconds",
                    delay
                )

                await asyncio.sleep(delay)

                backoff = min(backoff * 2, 60)

    async def stop(self):

        self.stop_event.set()

        if self.ws:
            await self.ws.close()
