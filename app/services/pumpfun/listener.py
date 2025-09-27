from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx
import websockets
from loguru import logger


PUMPFUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


@dataclass(frozen=True)
class PumpToken:
    mint: str


class PumpfunListener:
    def __init__(self, ws_rpc_url: str, http_rpc_url: str) -> None:
        self.ws_rpc_url = ws_rpc_url
        self.http_rpc_url = http_rpc_url
        self._stop = asyncio.Event()

    async def run(self, on_token: Callable[[PumpToken], Awaitable[None]]) -> None:
        while not self._stop.is_set():
            try:
                await self._consume(on_token)
            except Exception:
                logger.warning("PumpfunListener.run: reconnecting after error")
                await asyncio.sleep(2)

    async def stop(self) -> None:
        self._stop.set()

    async def _consume(self, on_token: Callable[[PumpToken], Awaitable[None]]) -> None:
        logger.debug("PumpfunListener: connecting WS {url}", url=self.ws_rpc_url)
        async with websockets.connect(
            self.ws_rpc_url,
            ping_interval=45,
            ping_timeout=45,
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
                    logger.trace("PumpfunListener: non-log msg: {m}", m=raw)
                    continue
                value = msg["params"]["result"]["value"]
                signature = value.get("signature")
                logs = value.get("logs") or []
                if not any("instruction: create" in (l or "").lower() for l in logs):
                    logger.trace("PumpfunListener: skip sig={s} no Create", s=signature)
                    continue
                logger.debug("PumpfunListener: Create detected sig={s}", s=signature)
                await self._wait_signature_available(signature)
                mint = await self._mint_from_signature(signature)
                if mint:
                    logger.info("PumpfunListener: mint extracted: {m}", m=mint)
                    await on_token(PumpToken(mint=mint))
                else:
                    logger.debug("PumpfunListener: mint not found for sig={s}", s=signature)

    async def _mint_from_signature(self, signature: str) -> str | None:
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
        for _ in range(40):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.post(self.http_rpc_url, json=payload)
                    data = r.json()
            except Exception:
                await asyncio.sleep(0.25)
                continue
            tx = (data or {}).get("result")
            if tx:
                break
            await asyncio.sleep(0.25)
        if not tx:
            logger.debug("PumpfunListener: no tx result for {s}", s=signature)
            return None
        msg = tx.get("transaction", {}).get("message", {})
        account_keys: list[str] = msg.get("accountKeys") or []
        loaded = msg.get("loadedAddresses") or {}
        resolved_keys: list[str] = account_keys + (loaded.get("writable") or []) + (loaded.get("readonly") or [])
        ix_list = msg.get("instructions") or []
        try:
            prog_idx = resolved_keys.index(PUMPFUN_PROGRAM_ID)
        except ValueError:
            logger.debug("PumpfunListener: program not in resolved_keys for {s}", s=signature)
            return None
        pump_ix = None
        for ix in ix_list:
            if ix.get("programIdIndex") == prog_idx:
                pump_ix = ix
                break
        if not pump_ix:
            logger.warning("PumpfunListener: no program instruction for {s}", s=signature)
            return None
        accounts_idx: list[int] = pump_ix.get("accounts") or []
        if len(accounts_idx) < 3:
            logger.debug("PumpfunListener: accounts too short for {s}", s=signature)
            return None
        mint_acc_idx = accounts_idx[2]
        if mint_acc_idx < 0 or mint_acc_idx >= len(resolved_keys):
            logger.debug("PumpfunListener: mint idx OOR for {s}", s=signature)
            return None
        return resolved_keys[mint_acc_idx]

    async def _wait_signature_available(self, signature: str) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignatureStatuses",
            "params": [[signature], {"searchTransactionHistory": True}],
        }
        for _ in range(40):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.post(self.http_rpc_url, json=payload)
                    data = r.json()
                value = (data or {}).get("result", {}).get("value", [])
                st = value[0] if value else None
                if st and st.get("confirmationStatus") in {"confirmed", "finalized"}:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.25)
