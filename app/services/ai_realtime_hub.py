"""Realtime fan-out for AI agent chat (local websockets + Redis pub/sub)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.core import ai_agent_metrics as metrics
from app.core.redis import get_redis, redis_available, redis_publish

logger = logging.getLogger(__name__)

_CHANNEL_PREFIX = "ai:rt:"

_local: dict[tuple[int, str], set[WebSocket]] = {}
_lock = asyncio.Lock()
_pubsub_task: asyncio.Task | None = None


def channel_for(user_id: int, agent_type: str) -> str:
    return f"{_CHANNEL_PREFIX}{user_id}:{agent_type}"


async def subscribe(user_id: int, agent_type: str, ws: WebSocket) -> None:
    key = (user_id, agent_type)
    async with _lock:
        _local.setdefault(key, set()).add(ws)
    metrics.incr("ws_connect_total")


async def unsubscribe(user_id: int, agent_type: str, ws: WebSocket) -> None:
    key = (user_id, agent_type)
    async with _lock:
        sockets = _local.get(key)
        if not sockets:
            return
        sockets.discard(ws)
        if not sockets:
            _local.pop(key, None)


async def publish_ai_message(
    *,
    user_id: int,
    agent_type: str,
    payload: dict[str, Any],
) -> None:
    """Push a chat message event to subscribers (Redis or local)."""
    body = {
        "type": "ai_message",
        "agent_type": agent_type,
        "message": payload,
    }
    raw = json.dumps(body, ensure_ascii=False, default=str)
    if redis_available():
        # Other nodes (and this one via pubsub bridge) deliver to local sockets.
        await redis_publish(channel_for(user_id, agent_type), raw)
    else:
        await _fanout_local(user_id, agent_type, raw)
    metrics.incr("ws_publish_total")


async def _fanout_local(user_id: int, agent_type: str, raw: str) -> None:
    key = (user_id, agent_type)
    async with _lock:
        sockets = list(_local.get(key, set()))
    dead: list[WebSocket] = []
    for ws in sockets:
        try:
            if ws.client_state != WebSocketState.CONNECTED:
                dead.append(ws)
                continue
            await ws.send_text(raw)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await unsubscribe(user_id, agent_type, ws)


async def start_redis_pubsub_bridge(stop_event: asyncio.Event) -> None:
    """Forward Redis pub/sub events to local websockets (multi-instance)."""
    if not redis_available():
        logger.info("ai_realtime redis pubsub bridge skipped")
        await stop_event.wait()
        return

    client = get_redis()
    assert client is not None
    pubsub = client.pubsub()
    await pubsub.psubscribe(f"{_CHANNEL_PREFIX}*")
    logger.info("ai_realtime redis pubsub bridge started")

    try:
        while not stop_event.is_set():
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=1.5,
                )
            except TimeoutError:
                continue
            if not message or message.get("type") not in ("pmessage", "message"):
                continue
            data = message.get("data")
            channel = message.get("channel") or message.get("pattern")
            if not isinstance(data, str) or not isinstance(channel, str):
                continue
            # channel: ai:rt:{user_id}:{agent_type}
            try:
                rest = channel[len(_CHANNEL_PREFIX) :]
                user_s, agent_type = rest.split(":", 1)
                user_id = int(user_s)
            except Exception:
                continue
            await _fanout_local(user_id, agent_type, data)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("ai_realtime pubsub bridge failed")
    finally:
        try:
            await pubsub.aclose()
        except Exception:
            pass
        logger.info("ai_realtime redis pubsub bridge stopped")


async def safe_close(ws: WebSocket) -> None:
    try:
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.close()
    except (WebSocketDisconnect, Exception):
        pass
