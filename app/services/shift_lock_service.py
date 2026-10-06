"""
Distributed Lock Service using Redis.
Prevents race conditions when multiple doctors try to accept the same shift simultaneously.
"""
import redis.asyncio as aioredis
from app.core.config import settings

# Initialize async Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

class ShiftLockService:
    @staticmethod
    async def acquire_lock(shift_id: int, doctor_id: int, timeout_seconds: int = 10) -> bool:
        """
        Attempts to acquire a lock for a specific shift.
        Uses Redis SET NX (Set if Not Exists) for atomic operations.
        """
        lock_key = f"shift_lock:{shift_id}"
        # nx=True means "only set if key does not exist"
        # ex=timeout_seconds means "auto-expire lock after X seconds to prevent deadlocks"
        acquired = await redis_client.set(lock_key, str(doctor_id), nx=True, ex=timeout_seconds)
        return bool(acquired)
        
    @staticmethod
    async def release_lock(shift_id: int):
        """Releases the lock manually once the transaction is complete."""
        lock_key = f"shift_lock:{shift_id}"
        await redis_client.delete(lock_key)
        
    @staticmethod
    async def get_lock_owner(shift_id: int) -> str | None:
        """Returns the doctor_id currently holding the lock."""
        lock_key = f"shift_lock:{shift_id}"
        return await redis_client.get(lock_key)
