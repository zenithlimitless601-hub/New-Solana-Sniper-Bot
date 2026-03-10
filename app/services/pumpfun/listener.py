"""Pump.fun real-time token listener via Solana logsSubscribe RPC."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx
import websockets
from loguru import logger

PUMPFUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

_WS_PING_INTERVAL = 45
_WS_PING_TIMEOUT = 45
_RECONNECT_DELAY_S = 2
_POLL_INTERVAL_S = 0.25
_MAX_POLL_ATTEMPTS = 40
_HTTP_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class PumpToken:
    """Represents a newly detected Pump.fun token mint."""

    mint: str


class PumpfunListener:
    """Listens for new Pump.fun token mints via Solana logsSubscribe.

    Connects to a Solana WebSocket RPC, subscribes to logs mentioning
    the Pump.fun program, and extracts mint addresses from Create
    instructions.
    """

    def __init__(self, ws_rpc_url: str, http_rpc_url: str) -> None:
        self.ws_rpc_url = ws_rpc_url
        self.http_rpc_url = http_rpc_url
        self._stop = asyncio.Event()

    async def run(self, on_token: Callable[[PumpToken], Awaitable[None]]) -> None:
        """Main loop with auto-reconnect on failure."""
        while not self._stop.is_set():
            try:
                await self._consume(on_token)
            except Exception:
                logger.warning("PumpfunListener: reconnecting after error")
                await asyncio.sleep(_RECONNECT_DELAY_S)

    async def stop(self) -> None:
        """Signal the listener to stop."""
        self._stop.set()

    async def _consume(self, on_token: Callable[[PumpToken], Awaitable[None]]) -> None:
        """Subscribe to logs and process Create instructions."""
        async with websockets.connect(
            self.ws_rpc_url,
            ping_interval=_WS_PING_INTERVAL,
            ping_timeout=_WS_PING_TIMEOUT,
            close_timeout=5,
            open_timeout=10,
            max_queue=None,
        ) as ws:
            sub = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": [PUMPFUN_PROGRAM_ID]},
                    {"commitment": "confirmed"},
                ],
            }
            await ws.send(json.dumps(sub))
            ack = await ws.recv()
            logger.debug("PumpfunListener: subscribed: {ack}", ack=ack)
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                if msg.get("method") != "logsNotification":
                    continue
                value = msg["params"]["result"]["value"]
                signature = value.get("signature")
                logs = value.get("logs") or []
                if not any("instruction: create" in (log or "").lower() for log in logs):
                    continue
                logger.debug("PumpfunListener: Create detected sig={s}", s=signature)
                await self._wait_signature_available(signature)
                mint = await self._mint_from_signature(signature)
                if mint:
                    logger.info("PumpfunListener: mint={m}", m=mint)
                    await on_token(PumpToken(mint=mint))

    async def _mint_from_signature(self, signature: str) -> str | None:
        """Extract the mint address from a confirmed transaction."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "json", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"},
            ],
        }
        tx = None
        for _ in range(_MAX_POLL_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
                    r = await client.post(self.http_rpc_url, json=payload)
                    data = r.json()
            except Exception:
                await asyncio.sleep(_POLL_INTERVAL_S)
                continue
            tx = (data or {}).get("result")
            if tx:
                break
            await asyncio.sleep(_POLL_INTERVAL_S)
        if not tx:
            return None

        msg = tx.get("transaction", {}).get("message", {})
        account_keys: list[str] = msg.get("accountKeys") or []
        loaded = msg.get("loadedAddresses") or {}
        resolved_keys: list[str] = (
            account_keys + (loaded.get("writable") or []) + (loaded.get("readonly") or [])
        )

        try:
            prog_idx = resolved_keys.index(PUMPFUN_PROGRAM_ID)
        except ValueError:
            return None

        pump_ix = None
        for ix in msg.get("instructions") or []:
            if ix.get("programIdIndex") == prog_idx:
                pump_ix = ix
                break
        if not pump_ix:
            return None

        accounts_idx: list[int] = pump_ix.get("accounts") or []
        if len(accounts_idx) < 3:
            return None
        mint_acc_idx = accounts_idx[2]
        if 0 <= mint_acc_idx < len(resolved_keys):
            return resolved_keys[mint_acc_idx]
        return None

    async def _wait_signature_available(self, signature: str) -> None:
        """Poll until the signature is confirmed or finalized."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignatureStatuses",
            "params": [[signature], {"searchTransactionHistory": True}],
        }
        for _ in range(_MAX_POLL_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
                    r = await client.post(self.http_rpc_url, json=payload)
                    data = r.json()
                value = (data or {}).get("result", {}).get("value", [])
                st = value[0] if value else None
                if st and st.get("confirmationStatus") in {"confirmed", "finalized"}:
                    return
            except Exception:
                pass
            await asyncio.sleep(_POLL_INTERVAL_S)
