import json
import os
import secrets
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    def __init__(self) -> None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.prefix = "otbor:"

    async def get(self, key: str) -> Optional[str]:
        return await self.redis.get(f"{self.prefix}{key}")

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return await self.redis.set(f"{self.prefix}{key}", value, ex=ex)

    async def delete(self, key: str) -> bool:
        return await self.redis.delete(f"{self.prefix}{key}")

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(value), ex=ex)

    async def get_list(self, key: str) -> List[str]:
        return await self.redis.lrange(f"{self.prefix}{key}", 0, -1)

    async def set_list(self, key: str, values: List[str], ex: Optional[int] = None) -> bool:
        pipe = self.redis.pipeline()
        pipe.delete(f"{self.prefix}{key}")
        if values:
            pipe.rpush(f"{self.prefix}{key}", *values)
        if ex:
            pipe.expire(f"{self.prefix}{key}", ex)
        results = await pipe.execute()
        return True

    async def generate_invite_token(self, interviewer_id: int, faculty_id: int, expires_in: int = 86400) -> str:
        """Генерирует токен приглашения для собеседующего"""
        token = secrets.token_urlsafe(32)
        invite_data = {
            "interviewer_id": interviewer_id,
            "faculty_id": faculty_id,
            "type": "interviewer_invite"
        }
        await self.set_json(f"invite:{token}", invite_data, ex=expires_in)
        return token

    async def get_invite_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Получает данные приглашения по токену"""
        return await self.get_json(f"invite:{token}")

    async def delete_invite_token(self, token: str) -> bool:
        """Удаляет токен приглашения"""
        return await self.delete(f"invite:{token}")

    async def close(self) -> None:
        await self.redis.close()


# Cache keys
class CacheKeys:
    FACULTY_SHEETS = "faculty_sheets"
    PARTICIPANTS = "participants:{faculty}"
    INVITES = "invites:{token}"
    PENDING = "pending:{user_id}"
    BOT_USERNAME = "bot_username"
