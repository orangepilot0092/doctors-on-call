import json
from app.core.redis import get_redis_client

class BotState:
    STATES = {"IDLE": "IDLE", "WAITING_HPR_ID": "WAITING_HPR_ID", "WAITING_OTP": "WAITING_OTP", "ONBOARDED": "ONBOARDED"}

    @staticmethod
    async def get_state(phone: str) -> dict:
        redis = await get_redis_client()
        data = await redis.get(f"wa:state:{phone}")
        if not data: return {"state": BotState.STATES["IDLE"], "context": {}}
        return json.loads(data.decode('utf-8'))

    @staticmethod
    async def set_state(phone: str, state: str, context: dict = None):
        redis = await get_redis_client()
        payload = {"state": state, "context": context or {}}
        await redis.setex(f"wa:state:{phone}", 3600, json.dumps(payload))
