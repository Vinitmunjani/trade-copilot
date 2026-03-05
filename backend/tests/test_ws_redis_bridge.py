import asyncio
import json

import pytest

from app.api.ws import WebSocketManager


class FakeWebSocket:
    def __init__(self):
        self.sent_text = []

    async def send_text(self, message: str):
        self.sent_text.append(message)


class FakePubSub:
    def __init__(self, messages):
        self._messages = list(messages)
        self.patterns = []
        self.closed = False

    async def psubscribe(self, pattern: str):
        self.patterns.append(pattern)

    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        if self._messages:
            return self._messages.pop(0)
        await asyncio.sleep(0.01)
        return None

    async def close(self):
        self.closed = True


class FakeRedis:
    def __init__(self, pubsub_messages=None):
        self.published = []
        self._pubsub = FakePubSub(pubsub_messages or [])

    async def publish(self, channel: str, message: str):
        self.published.append((channel, message))

    def pubsub(self):
        return self._pubsub


@pytest.mark.asyncio
async def test_broadcast_to_user_sends_local_and_publishes_redis():
    manager = WebSocketManager()
    ws = FakeWebSocket()
    manager._connections["user-1"] = [ws]
    redis_client = FakeRedis()
    manager._redis_client = redis_client

    payload = {"type": "ai_review_stream", "trade_id": "t1", "status": "chunk", "chunk": "hello"}
    await manager.broadcast_to_user("user-1", payload)

    assert len(ws.sent_text) == 1
    local_data = json.loads(ws.sent_text[0])
    assert local_data["type"] == "ai_review_stream"
    assert "_source_instance" not in local_data

    assert len(redis_client.published) == 1
    channel, raw = redis_client.published[0]
    assert channel == "ws:user:user-1"
    published_data = json.loads(raw)
    assert published_data["type"] == "ai_review_stream"
    assert published_data["_source_instance"] == manager._instance_id


@pytest.mark.asyncio
async def test_redis_bridge_forwards_other_instance_message_to_local_socket():
    manager = WebSocketManager()
    ws = FakeWebSocket()
    manager._connections["user-42"] = [ws]

    incoming_payload = {
        "type": "ai_review_stream",
        "trade_id": "trade-99",
        "status": "chunk",
        "chunk": "partial review",
        "_source_instance": "other-instance",
    }

    redis_client = FakeRedis(pubsub_messages=[
        {
            "type": "pmessage",
            "channel": "ws:user:user-42",
            "data": json.dumps(incoming_payload),
        }
    ])

    await manager.start_redis_bridge(redis_client)
    await asyncio.sleep(0.05)
    await manager.stop_redis_bridge()

    assert len(ws.sent_text) >= 1
    forwarded = json.loads(ws.sent_text[0])
    assert forwarded["type"] == "ai_review_stream"
    assert forwarded["trade_id"] == "trade-99"
    assert forwarded["chunk"] == "partial review"
    assert "_source_instance" not in forwarded

    assert redis_client._pubsub.patterns == ["ws:user:*"]
    assert redis_client._pubsub.closed is True
