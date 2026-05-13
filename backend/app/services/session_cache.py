import json
from uuid import UUID
from typing import Optional, Any, Dict
import redis.asyncio as aioredis
from app.core.config import settings

class SessionCache:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours

    def _get_key(self, session_id: UUID) -> str:
        return f"session:{session_id}"

    async def set_state(self, session_id: UUID, state: Dict[str, Any]) -> None:
        """
        Store session state in Redis.
        """
        key = self._get_key(session_id)
        await self.redis.set(key, json.dumps(state), ex=self.ttl)

    async def get_state(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state from Redis.
        """
        key = self._get_key(session_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def update_state(self, session_id: UUID, updates: Dict[str, Any]) -> None:
        """
        Partial update of session state.
        """
        current = await self.get_state(session_id) or {}
        current.update(updates)
        await self.set_state(session_id, current)

    async def delete_state(self, session_id: UUID) -> None:
        """
        Remove session state from cache.
        """
        key = self._get_key(session_id)
        await self.redis.delete(key)
