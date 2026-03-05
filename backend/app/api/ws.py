"""WebSocket endpoint for real-time trade events.

Authenticates via JWT token query parameter, maintains per-user connections,
and broadcasts trade events, AI scores, and behavioral alerts.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, List,  Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections per user.

    Maintains a registry of active WebSocket connections indexed by user ID,
    allowing targeted broadcasting of events to specific users.
    """

    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}
        self._instance_id = str(uuid.uuid4())
        self._redis_client = None
        self._redis_bridge_task: Optional[asyncio.Task] = None

    async def start_redis_bridge(self, redis_client: Any) -> None:
        """Start Redis pub/sub bridge for cross-instance fanout."""
        if not redis_client or self._redis_bridge_task:
            return
        self._redis_client = redis_client
        self._redis_bridge_task = asyncio.create_task(self._run_redis_bridge())
        logger.info(f"Redis WS bridge started (instance={self._instance_id})")

    async def stop_redis_bridge(self) -> None:
        """Stop Redis pub/sub bridge task."""
        if self._redis_bridge_task:
            self._redis_bridge_task.cancel()
            try:
                await self._redis_bridge_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Redis WS bridge stopped with error")
            self._redis_bridge_task = None
            logger.info("Redis WS bridge stopped")

    async def _run_redis_bridge(self) -> None:
        """Listen to Redis pub/sub and forward messages to local sockets."""
        if not self._redis_client:
            return

        pubsub = self._redis_client.pubsub()
        try:
            await pubsub.psubscribe("ws:user:*")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    await asyncio.sleep(0.01)
                    continue

                if message.get("type") not in ("pmessage", "message"):
                    continue

                channel = message.get("channel", "")
                if not isinstance(channel, str) or not channel.startswith("ws:user:"):
                    continue

                user_id = channel.replace("ws:user:", "", 1)
                payload_raw = message.get("data")
                if payload_raw is None:
                    continue

                try:
                    payload = json.loads(payload_raw)
                except Exception:
                    continue

                source_instance = payload.get("_source_instance") if isinstance(payload, dict) else None
                if source_instance == self._instance_id:
                    continue

                if isinstance(payload, dict):
                    payload.pop("_source_instance", None)
                    await self._broadcast_local_to_user(user_id, payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis WS bridge listener error")
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            user_id: User UUID string.
            websocket: FastAPI WebSocket instance.
        """
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id} (total: {len(self._connections[user_id])})")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            user_id: User UUID string.
            websocket: WebSocket to remove.
        """
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws != websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def broadcast_to_user(self, user_id: str, data: dict) -> None:
        """Send a message to all WebSocket connections for a specific user.

        Args:
            user_id: Target user UUID string.
            data: Dict to serialize as JSON and send.
        """
        await self._broadcast_local_to_user(user_id, data)

        if self._redis_client:
            try:
                payload = dict(data)
                payload["_source_instance"] = self._instance_id
                message = json.dumps(payload, default=str)
                await self._redis_client.publish(f"ws:user:{user_id}", message)
            except Exception:
                logger.exception(f"Failed to publish WS message to Redis for user {user_id}")

    async def _broadcast_local_to_user(self, user_id: str, data: dict) -> None:
        """Send a message only to local process WebSocket connections."""
        if user_id not in self._connections:
            return

        message = json.dumps(data, default=str)
        dead_connections = []

        for ws in self._connections[user_id]:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket for user {user_id}: {e}")
                dead_connections.append(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self._connections[user_id] = [
                w for w in self._connections[user_id] if w != ws
            ]
        if user_id in self._connections and not self._connections[user_id]:
            del self._connections[user_id]

    async def broadcast_all(self, data: dict) -> None:
        """Broadcast a message to all connected users.

        Args:
            data: Dict to serialize as JSON and send.
        """
        for user_id in list(self._connections.keys()):
            await self.broadcast_to_user(user_id, data)

    def get_connected_users(self) -> List[str]:
        """Return list of user IDs with active WebSocket connections.

        Returns:
            List of user UUID strings.
        """
        return list(self._connections.keys())

    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user.

        Args:
            user_id: User UUID string.

        Returns:
            Number of active WebSocket connections.
        """
        return len(self._connections.get(user_id, []))


# Global singleton
ws_manager = WebSocketManager()


@router.websocket("/ws/trades")
async def websocket_trades(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
):
    """WebSocket endpoint for real-time trade events.

    Authenticates via JWT token in query params. Maintains a persistent
    connection that receives:
    - TRADE_OPENED: New trade with AI score
    - TRADE_UPDATED: Trade modification (SL/TP change)
    - TRADE_CLOSED: Trade closed with AI review
    - BEHAVIORAL_ALERT: Trading psychology warning
    - MARKET_UPDATE: Market context changes

    Query Params:
        token: JWT authentication token.
    """
    # Authenticate
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Connect
    await ws_manager.connect(user_id, websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "CONNECTED",
            "message": "WebSocket connection established",
            "user_id": user_id,
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Could handle client commands here in the future
                    logger.debug(f"Received from user {user_id}: {data}")
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await ws_manager.disconnect(user_id, websocket)
