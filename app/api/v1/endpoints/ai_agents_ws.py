"""WebSocket stream for live AI agent chat matches."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_token
from app.db.session import async_session_maker
from app.models.ai_enums import AiAgentType
from app.repositories.user_repository import UserRepository
from app.services import ai_realtime_hub as hub

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{agent_type}")
async def ai_agent_ws(websocket: WebSocket, agent_type: AiAgentType) -> None:
    token = websocket.query_params.get("token") or ""
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        user_id = int(sub)
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4401)
        return

    async with async_session_maker() as session:
        user = await UserRepository(session).get_by_id(user_id)
        if user is None:
            await websocket.close(code=4401)
            return

    await websocket.accept()
    await hub.subscribe(user_id, agent_type.value, websocket)
    try:
        await websocket.send_json({"type": "ready", "agent_type": agent_type.value})
        while True:
            # Keepalive / ignore client pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ai_agent_ws error user_id=%s agent=%s", user_id, agent_type.value)
    finally:
        await hub.unsubscribe(user_id, agent_type.value, websocket)
        await hub.safe_close(websocket)
