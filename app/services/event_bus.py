import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings


_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def facility_channel(facility_id: int) -> str:
    return f"facility:{facility_id}"


def global_channel() -> str:
    return "global"


async def publish_event(channel: str, event: dict[str, Any]) -> dict[str, Any]:
    """
    Publish a JSON event to a Redis channel.
    """
    redis = get_redis()
    payload = {
        "channel": channel,
        "event": event,
    }
    await redis.publish(channel, json.dumps(payload, default=str))
    return payload


async def subscribe_events(channel: str):
    """
    Async generator that yields raw JSON strings from a Redis channel.
    """
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
